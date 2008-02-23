# encoding: utf-8
# -*- test-case-name: ipython1.kernel.test.test_multiengineclient -*-
"""General Classes for IMultiEngine clients.
"""
__docformat__ = "restructuredtext en"
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelley <benjaminrk@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import sys
import cPickle as pickle
from types import FunctionType

from twisted.internet import reactor
from twisted.python import components, log
from twisted.python.failure import Failure
from zope.interface import Interface, implements, Attribute

from IPython.ColorANSI import TermColors

from ipython1.kernel.twistedutil import blockingCallFromThread
from ipython1.kernel import error
from ipython1.kernel.parallelfunction import ParallelFunction
from ipython1.kernel import map as Map
from ipython1.kernel import multiengine as me
from ipython1.kernel.multiengine import (IFullMultiEngine,
    IFullSynchronousMultiEngine)


#-------------------------------------------------------------------------------
# Pending Result things
#-------------------------------------------------------------------------------

class IPendingResult(Interface):
    """A representation of a result that is pending.
    
    This class is similar to Twisted's Deferred object, but is designed to be
    used in a synchronous context.
    """
    
    result_id=Attribute("ID of the deferred on the other side")
    client=Attribute("A client that I came from")
    r=Attribute("An attribute that is a property that calls and returns get_result")
    
    def get_result(default=None, block=True):
        """Get a result that is pending.
                
        :Parameters:
            default
                The value to return if the result is not ready.
            block : boolean
                Should I block for the result.
                
        :Returns: The actual result or the default value.
        """
        
    def add_callback(f, *args, **kwargs):
        """Add a callback that is called with the result.
        
        If the original result is foo, adding a callback will cause
        f(foo, *args, **kwargs) to be returned instead.  If multiple
        callbacks are registered, they are chained together: the result of
        one is passed to the next and so on.  
        
        Unlike Twisted's Deferred object, there is no errback chain.  Thus
        any exception raised will not be caught and handled.  User must 
        catch these by hand when calling `get_result`.
        """


class PendingResult(object):
    """A representation of a result that is not yet ready.
    
    A user should not create a `PendingResult` instance by hand.  They are returned
    by methods of ISynchronousMultiEngine clients.
    
    Methods
    =======
    
    * `get_result`
    * `add_callback`
    
    Properties
    ==========
    * `r`
    """
    
    def __init__(self, client, result_id):
        """Create a PendingResult with a result_id and a client instance.
        
        The client should implement `_getPendingResult(result_id, block)`.
        """
        self.client = client
        self.result_id = result_id
        self.called = False
        self.raised = False
        self.callbacks = []
        
    def get_result(self, default=None, block=True):
        """Get a result that is pending.
                
        This method will connect to an IMultiEngine adapted controller
        and see if the result is ready.  If the action triggers an exception
        raise it and record it.  This method records the result/exception once it is 
        retrieved.  Calling `get_result` again will get this cached result or will
        re-raise the exception.  The .r attribute is a property that calls
        `get_result` with block=True.
        
        :Parameters:
            default
                The value to return if the result is not ready.
            block : boolean
                Should I block for the result.
                
        :Returns: The actual result or the default value.
        """
        
        if self.called:
            if self.raised:
                raise self.result[0], self.result[1], self.result[2]
            else:
                return self.result
        try:
            result = self.client.get_pending_deferred(self.result_id, block)
        except error.ResultNotCompleted:
            return default
        except:
            # Reraise other error, but first record them so they can be reraised
            # later if .r or get_result is called again.
            self.result = sys.exc_info()
            self.called = True
            self.raised = True
            raise
        else:
            for cb in self.callbacks:
                result = cb[0](result, *cb[1], **cb[2])
            self.result = result
            self.called = True
            return result
        
    def add_callback(self, f, *args, **kwargs):
        """Add a callback that is called with the result.
        
        If the original result is result, adding a callback will cause
        f(result, *args, **kwargs) to be returned instead.  If multiple
        callbacks are registered, they are chained together: the result of
        one is passed to the next and so on.  
        
        Unlike Twisted's Deferred object, there is no errback chain.  Thus
        any exception raised will not be caught and handled.  User must 
        catch these by hand when calling `get_result`.
        """
        assert callable(f)
        self.callbacks.append((f, args, kwargs))
        
    def __cmp__(self, other):
        if self.result_id < other.result_id:
            return -1
        else:
            return 1
            
    def _get_r(self):
        return self.get_result(block=True)
    
    r = property(_get_r)
    """This property is a shortcut to a `get_result(block=True)`."""


#-------------------------------------------------------------------------------
# Pretty printing wrappers for certain lists
#-------------------------------------------------------------------------------    
    
class ResultList(list):
    """A subclass of list that pretty prints the output of `execute`/`get_result`."""
    
    def __repr__(self):
        output = []
        blue = TermColors.Blue
        normal = TermColors.Normal
        red = TermColors.Red
        green = TermColors.Green
        output.append("<Results List>\n")
        for cmd in self:
            if isinstance(cmd, Failure):
                output.append(cmd)
            else:
                target = cmd.get('id',None)
                cmd_num = cmd.get('number',None)
                cmd_stdin = cmd.get('input',{}).get('translated','No Input')
                cmd_stdout = cmd.get('stdout', None)
                cmd_stderr = cmd.get('stderr', None)
                output.append("%s[%i]%s In [%i]:%s %s\n" % \
                    (green, target,
                    blue, cmd_num, normal, cmd_stdin))
                if cmd_stdout:
                    output.append("%s[%i]%s Out[%i]:%s %s\n" % \
                        (green, target,
                        red, cmd_num, normal, cmd_stdout))
                if cmd_stderr:
                    output.append("%s[%i]%s Err[%i]:\n%s %s" % \
                        (green, target,
                        red, cmd_num, normal, cmd_stderr))
        return ''.join(output)


def wrapResultList(result):
    """A function that wraps the output of `execute`/`get_result` -> `ResultList`."""
    if len(result) == 0:
        result = [result]
    return ResultList(result)


class QueueStatusList(list):
    """A subclass of list that pretty prints the output of `queue_status`."""
    
    def __repr__(self):
        output = []
        output.append("<Queue Status List>\n")
        for e in self:
            output.append("Engine: %s\n" % repr(e[0]))
            output.append("    Pending: %s\n" % repr(e[1]['pending']))
            for q in e[1]['queue']:
                output.append("    Command: %s\n" % repr(q))
        return ''.join(output)


#-------------------------------------------------------------------------------
# InteractiveMultiEngineClient
#-------------------------------------------------------------------------------    

class InteractiveMultiEngineClient(object):
                                        
    def activate(self):
        """Make this `RemoteController` active for parallel magic commands.
        
        IPython has a magic command syntax to work with `RemoteController` objects.
        In a given IPython session there is a single active one.  While
        there can be many `RemoteController` created and used by the user, 
        there is only one active one.  The active `RemoteController` is used whenever 
        the magic commands %px and %autopx are used.
        
        The activate() method is called on a given `RemoteController` to make it 
        active.  Once this has been done, the magic commands can be used.
        
        Examples
        
        >>> rc = RemoteController(('localhost',10000))
        >>> rc.activate()
        >>> %px a = 5       # Same as executeAll('a = 5')        
        >>> %autopx         # Now every command is sent to execute()
        ...
        >>> %autopx         # The second time it toggles autoparallel mode off
        """
        
        try:
            __IPYTHON__.activeController = self
        except NameError:
            print "The IPython Controller magics only work within IPython."
                    
    def __setitem__(self, key, value):
        """Add a dictionary interface for pushing/pulling.
        
        This functions as a shorthand for `pushAll`.
        
        Examples:
        
        >>> rc = RemoteController(('localhost',10000))
        >>> rc['a'] = 10                      # Same as rc.pushAll(a=10)
        
        :Parameters:
            key : str 
                What to call the remote object.
            value : object
                The local Python object to push.
        """
        targets, block = self._findTargetsAndBlock()
        return self.push({key:value}, targets=targets, block=block)
    
    def __getitem__(self, key):
        """Add a dictionary interface for pushing/pulling.
        
        This functions as a shorthand to `pullAll`.
        
        >>> rc = RemoteController(('localhost',10000))
        >>> rc['a']                     # Same as rc.pullAll('a')
        (10, 10, 10, 10)
        
        :Parameters:
         - `id`: A string representing the key.
        """
        if isinstance(key, str):
            targets, block = self._findTargetsAndBlock()
            return self.pull(key, targets=targets, block=block)
        else:
            raise TypeError("__getitem__ only takes strs")
            
    def __len__(self):
        """Return the number of available engines."""
        return len(self.get_ids())
        
    def parallelize(self, func, targets=None, block=None):
        """Build a `ParallelFunction` object for functionName on engines.
        
        The returned object will implement a parallel version of functionName
        that takes a local sequence as its only argument and calls (in 
        parallel) functionName on each element of that sequence.  The
        `ParallelFunction` object has a `targets` attribute that controls
        which engines the function is run on.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `get_ids` to see
                a list of currently available engines.
            functionName : str
                A Python string that names a callable defined on the engines.
        
        :Returns:  A `ParallelFunction` object.                
        
        Examples
        ========
        
        >>> psin = rc.parallelize('all','lambda x:sin(x)')
        >>> psin(range(10000))
        [0,2,4,9,25,36,...]
        """
        targets, block = self._findTargetsAndBlock(targets, block)
        return ParallelFunction(func, self, targets, block)


#-------------------------------------------------------------------------------
# IFullTwoPhaseMultiEngine -> IFullBlockingMultiEngineClient adaptor
#-------------------------------------------------------------------------------


class IFullBlockingMultiEngineClient(Interface):
    pass


class FullBlockingMultiEngineClient(InteractiveMultiEngineClient):
    
    implements(IFullBlockingMultiEngineClient)
    
    def __init__(self, smultiengine):
        self.smultiengine = smultiengine
        self.block = True
        self.targets = 'all'
    
    def _findBlock(self, block=None):
        if block is None:
            return self.block
        else:
            if block in (True, False):
                return block
            else:
                raise ValueError("block must be True or False")
    
    def _findTargets(self, targets=None):
        if targets is None:
            return self.targets
        else:
            if not isinstance(targets, (str,list,tuple,int)):
                raise ValueError("targets must be a str, list, tuple or int")
            return targets
    
    def _findTargetsAndBlock(self, targets=None, block=None):
        return self._findTargets(targets), self._findBlock(block) 
    
    def _blockFromThread(self, function, *args, **kwargs):
        block = kwargs.get('block', None)
        if block is None:
            raise error.MissingBlockArgument("'block' keyword argument is missing")
        result = blockingCallFromThread(function, *args, **kwargs)
        if not block:
            result = PendingResult(self, result)
        return result
    
    def get_pending_deferred(self, deferredID, block):
        return blockingCallFromThread(self.smultiengine.get_pending_deferred, deferredID, block)
    
    def barrier(self, pendingResults):
        """Synchronize a set of `PendingResults`.
        
        This method is a synchronization primitive that waits for a set of
        `PendingResult` objects to complete.  More specifically, barier does
        the following.
        
        * The `PendingResult`s are sorted by result_id.
        * The `get_result` method is called for each `PendingResult` sequentially
          with block=True.
        * If a `PendingResult` gets a result that is an exception, it is 
          trapped and can be re-raised later by calling `get_result` again.
        * The `PendingResult`s are flushed from the controller.
                
        After barrier has been called on a `PendingResult`, its results can 
        be retrieved by calling `get_result` again or accesing the `r` attribute
        of the instance.
        """
        
        # Convert to list for sorting and check class type 
        prList = list(pendingResults)
        for pr in prList:
            if not isinstance(pr, PendingResult):
                raise error.NotAPendingResult("Objects passed to barrier must be PendingResult instances")
                            
        # Sort the PendingResults so they are in order
        prList.sort()
        # Block on each PendingResult object
        for pr in prList:
            try:
                result = pr.get_result(block=True)
            except Exception:
                pass
    
    def flush(self):
        r = blockingCallFromThread(self.smultiengine.clean_out_deferreds)
        return r
    
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
    
    def execute(self, lines, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        result = blockingCallFromThread(self.smultiengine.execute, lines,
            targets=targets, block=block)
        if block:
            result = ResultList(result)
        else:
            result = PendingResult(self, result)
            result.add_callback(wrapResultList)
        return result
    
    def push(self, namespace, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.push, namespace,
            targets=targets, block=block)
    
    def pull(self, keys, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.pull, keys, targets=targets, block=block)
    
    def push_function(self, namespace, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.push_function, namespace, targets=targets, block=block)
    
    def pull_function(self, keys, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.pull_function, keys, targets=targets, block=block)
    
    def push_serialized(self, namespace, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.push_serialized, namespace, targets=targets, block=block)
    
    def pull_serialized(self, keys, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.pull_serialized, keys, targets=targets, block=block)
    
    def get_result(self, i=None, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        result = blockingCallFromThread(self.smultiengine.get_result, i, targets=targets, block=block)
        if block:
            result = ResultList(result)
        else:
            result = PendingResult(self, result)
            result.add_callback(wrapResultList)
        return result
    
    def reset(self, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.reset, targets=targets, block=block)
    
    def keys(self, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.keys, targets=targets, block=block)
    
    def kill(self, controller=False, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.kill, controller, targets=targets, block=block)
    
    def clear_queue(self, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.clear_queue, targets=targets, block=block)
    
    def queue_status(self, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.queue_status, targets=targets, block=block)
    
    def set_properties(self, properties, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.set_properties, properties, targets=targets, block=block)
    
    def get_properties(self, keys=None, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.get_properties, keys, targets=targets, block=block)
    
    def has_properties(self, keys, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.has_properties, keys, targets=targets, block=block)
    
    def del_properties(self, keys, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.del_properties, keys, targets=targets, block=block)
    
    def clear_properties(self, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.clear_properties, targets=targets, block=block)
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def get_ids(self):
        result = blockingCallFromThread(self.smultiengine.get_ids)
        return result
        
    #---------------------------------------------------------------------------
    # IMultiEngineCoordinator
    #---------------------------------------------------------------------------
             
    def scatter(self, key, seq, style='basic', flatten=False, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.scatter, key, seq, 
            style, flatten, targets=targets, block=block)
    
    def gather(self, key, style='basic', targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.gather, key, style, 
            targets=targets, block=block)
    
    def map(self, func, seq, style='basic', targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.map, func, seq, 
            style, targets=targets, block=block)
    
    #---------------------------------------------------------------------------
    # IMultiEngineExtras
    #---------------------------------------------------------------------------
    
    def zip_pull(self, keys, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.zip_pull, keys, 
            targets=targets, block=block)
    
    def run(self, fname, targets=None, block=None):
        targets, block = self._findTargetsAndBlock(targets, block)
        return self._blockFromThread(self.smultiengine.run, fname,
            targets=targets, block=block)



components.registerAdapter(FullBlockingMultiEngineClient,
            IFullSynchronousMultiEngine, IFullBlockingMultiEngineClient)


#-------------------------------------------------------------------------------
# IFullSynchronousMultiEngine -> IFullBlockingMultiEngineClient adaptor
#-------------------------------------------------------------------------------

# def mainClientAdaptor(smultiengine):
#     client = IFullBlockingMultiEngineClient(smultiengine)
#     return client
# 
# components.registerAdapter(mainClientAdaptor,
#             me.IFullSynchronousMultiEngine, IFullBlockingMultiEngineClient)

#-------------------------------------------------------------------------------
# IFullSynchronousMultiEngine -> IFullSynchronousMultiEngine adaptor
#-------------------------------------------------------------------------------

# def mainAsynClientAdaptor(smultiengine):
#     return smultiengine
# 
# components.registerAdapter(mainAsynClientAdaptor,
#             me.IFullSynchronousMultiEngine, me.IFullSynchronousMultiEngine)




