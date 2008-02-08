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
from ipython1.kernel.pendingdeferred import PendingDeferredManager, twoPhase
from ipython1.kernel import multiengine as me
from ipython1.kernel.multiengine import \
    IFullMultiEngine, \
    EngineMultiplexerAll, \
    IFullSynchronousMultiEngine, \
    IFullSynchronousTwoPhaseMultiEngine


#-------------------------------------------------------------------------------
# Pending Result things
#-------------------------------------------------------------------------------

class IPendingResult(Interface):
    """A representation of a result that is pending.
    
    This class is similar to Twisted's Deferred object, but is designed to be
    used in a synchronous context.
    """
    
    resultID=Attribute("ID of the deferred on the other side")
    client=Attribute("An ISynchronousMultiEngineClient that I came from")
    r=Attribute("An attribute that is a property that calls and returns getResult")
    
    def getResult(default=None, block=True):
        """Get a result that is pending.
                
        :Parameters:
            default
                The value to return if the result is not ready.
            block : boolean
                Should I block for the result.
                
        :Returns: The actual result or the default value.
        """
        
    def addCallback(f, *args, **kwargs):
        """Add a callback that is called with the result.
        
        If the original result is foo, adding a callback will cause
        f(foo, *args, **kwargs) to be returned instead.  If multiple
        callbacks are registered, they are chained together: the result of
        one is passed to the next and so on.  
        
        Unlike Twisted's Deferred object, there is no errback chain.  Thus
        any exception raised will not be caught and handled.  User must 
        catch these by hand when calling `getResult`.
        """

class PendingResult(object):
    """A representation of a result that is not yet ready.
    
    A user should not create a `PendingResult` instance by hand.  They are returned
    by methods of ISynchronousMultiEngine clients.
    
    Methods
    =======
    
    * `getResult`
    * `addCallback`
    
    Properties
    ==========
    * `r`
    """
    
    def __init__(self, client, resultID):
        """Create a PendingResult with a resultID and a client instance.
        
        The client should implement `_getPendingResult(resultID, block)`.
        """
        self.client = client
        self.resultID = resultID
        self.called = False
        self.raised = False
        self.callbacks = []
        
    def getResult(self, default=None, block=True):
        """Get a result that is pending.
                
        This method will connect to an IMultiEngine adapted controller
        and see if the result is ready.  If the action triggers an exception
        raise it and record it.  This method records the result/exception once it is 
        retrieved.  Calling `getResult` again will get this cached result or will
        re-raise the exception.  The .r attribute is a property that calls
        `getResult` with block=True.
        
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
            result = self.client.getPendingDeferred(self.resultID, block)
        except error.ResultNotCompleted:
            return default
        except:
            # Reraise other error, but first record them so they can be reraised
            # later if .r or getResult is called again.
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
        
    def addCallback(self, f, *args, **kwargs):
        """Add a callback that is called with the result.
        
        If the original result is result, adding a callback will cause
        f(result, *args, **kwargs) to be returned instead.  If multiple
        callbacks are registered, they are chained together: the result of
        one is passed to the next and so on.  
        
        Unlike Twisted's Deferred object, there is no errback chain.  Thus
        any exception raised will not be caught and handled.  User must 
        catch these by hand when calling `getResult`.
        """
        assert callable(f)
        self.callbacks.append((f, args, kwargs))
        
    def __cmp__(self, other):
        return self.resultID - other.resultID
        
    def _get_r(self):
        return self.getResult(block=True)

    r = property(_get_r)
    """This property is a shortcut to a `getResult(block=True)`."""
        
        
#-------------------------------------------------------------------------------
# Pretty printing wrappers for certain lists
#-------------------------------------------------------------------------------    
    
class ResultList(list):
    """A subclass of list that pretty prints the output of `execute`/`getResult`."""
    
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
    """A function that wraps the output of `execute`/`getResult` -> `ResultList`."""
    if len(result) == 0:
        result = [result]
    return ResultList(result)
    
class QueueStatusList(list):
    """A subclass of list that pretty prints the output of `queueStatus`."""

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
        
    _magicTargets = 'all'
    
    def _setMagicTargets(self, targets):
        self._magicTargets = targets
        
    def _getMagicTargets(self):
        return self._magicTargets
    
    magicTargets = property(_getMagicTargets, _setMagicTargets, None, None)
                                
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
        return self.push('all', **{key:value})
    
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
            return self.pull('all', *(key,))
        else:
            raise TypeError("__getitem__ only takes strs")
            
    def __len__(self):
        """Return the number of available engines."""
        return len(self.getIDs())
        
    def parallelize(self, targets, functionName):
        """Build a `ParallelFunction` object for functionName on engines.
        
        The returned object will implement a parallel version of functionName
        that takes a local sequence as its only argument and calls (in 
        parallel) functionName on each element of that sequence.  The
        `ParallelFunction` object has a `targets` attribute that controls
        which engines the function is run on.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `getIDs` to see
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
        
        return ParallelFunction(targets, functionName, self)
        
    def parallelizeAll(self, functionName):
        """Build a `ParallelFunction` that operates on all engines.
        
        See the docstring for `parallelize` for more details.
        """
        return self.parallelize('all', functionName)


#-------------------------------------------------------------------------------
# IFullTwoPhaseMultiEngine -> IFullBlockingMultiEngineClient adaptor
#-------------------------------------------------------------------------------


class IFullBlockingMultiEngineClient(Interface):
    pass


class FullBlockingMultiEngineClient(InteractiveMultiEngineClient, EngineMultiplexerAll):
    
    implements(IFullBlockingMultiEngineClient)
    
    def __init__(self, stpmultiengine):
        self.stpmultiengine = stpmultiengine
        self.block = True
    
    def _reallyBlock(self, block=None):
        if block is None:
            return self.block
        else:
            if block in (True, False):
                return block
            else:
                raise ValueError("block must be True or False")
    
    def _blockFromThread(self, function, *args, **kwargs):
        block = self._reallyBlock()
        result = blockingCallFromThread(function, block, *args, **kwargs)
        if not block:
            result = PendingResult(self, result)
        return result
    
    def getPendingDeferred(self, deferredID, block):
        return blockingCallFromThread(self.stpmultiengine.getPendingDeferred, deferredID, block)
    
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
    
    def execute(self, targets, lines, block=None):
        block = self._reallyBlock(block)
        result = blockingCallFromThread(self.stpmultiengine.execute, block,
            targets, lines)
        if block:
            result = ResultList(result)
        else:
            result = PendingResult(self, result)
            result.addCallback(wrapResultList)
        return result
    
    def executeAll(self, lines, block=None):
        return self.execute('all', lines, block)
    
    def push(self, targets, **namespace):
        return self._blockFromThread(self.stpmultiengine.push, targets, **namespace)
    
    def pull(self, targets, *keys):
        return self._blockFromThread(self.stpmultiengine.pull, targets, *keys)
    
    def pushFunction(self, targets, **namespace):
        return self._blockFromThread(self.stpmultiengine.pushFunction, targets, **namespace)
    
    def pullFunction(self, targets, *keys):
        return self._blockFromThread(self.stpmultiengine.pullFunction, targets, *keys)
    
    def pushSerialized(self, targets, **namespace):
        return self._blockFromThread(self.stpmultiengine.pushSerialized, targets, **namespace)
    
    def pullSerialized(self, targets, *keys):
        return self._blockFromThread(self.stpmultiengine.pullSerialized, targets, *keys)
    
    def getResult(self, targets, i=None):
        block = self._reallyBlock()
        result = blockingCallFromThread(self.stpmultiengine.getResult, block,
            targets, lines)
        if block:
            result = ResultList(result)
        else:
            result = PendingResult(self, result)
            result.addCallback(wrapResultList)
        return result
    
    def reset(self, targets):
        return self._blockFromThread(self.stpmultiengine.reset, targets)
    
    def keys(self, targets):
        return self._blockFromThread(self.stpmultiengine.keys, targets)
    
    def kill(self, targets, controller=False):
        return self._blockFromThread(self.stpmultiengine.kill, targets)
    
    def clearQueue(self, targets):
        return self._blockFromThread(self.stpmultiengine.clearQueue, targets)
    
    def queueStatus(self, targets):
        return self._blockFromThread(self.stpmultiengine.queueStatus, targets)
    
    def setProperties(self, targets, **properties):
        return self._blockFromThread(self.stpmultiengine.setProperties, targets)
    
    def getProperties(self, targets, *keys):
        return self._blockFromThread(self.stpmultiengine.getProperties, targets, *keys)
    
    def hasProperties(self, targets, *keys):
        return self._blockFromThread(self.stpmultiengine.hasProperties, targets, *keys)
    
    def delProperties(self, targets, *keys):
        return self._blockFromThread(self.stpmultiengine.delProperties, targets, *keys)
    
    def clearProperties(self, targets):
        return self._blockFromThread(self.stpmultiengine.clearProperties, targets, *keys)
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def getIDs(self):
        return self._blockFromThread(self.stpmultiengine.getIDs, targets)
    
    #---------------------------------------------------------------------------
    # IMultiEngineCoordinator
    #---------------------------------------------------------------------------
             
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        return self._blockFromThread(self.stpmultiengine.scatter, targets, 
            key, seq, style, flatten)
    
    def scatterAll(self, key, seq, style='basic', flatten=False):
        return self.scatter('all', key, seq, style, flatten)
        
    def gather(self, targets, key, style='basic'):
        return self._blockFromThread(self.stpmultiengine.gather, targets, 
            key, style)
        
    def gatherAll(self, key, style='basic'):
        return self.gather('all', key, style)
            
    def map(self, targets, func, seq, style='basic'):
        return self._blockFromThread(self.stpmultiengine.map, targets, func, 
            seq, style)
    
    def mapAll(self, func, seq, style='basic'):
        return self.map('all', func, seq, style)
    
    #---------------------------------------------------------------------------
    # IMultiEngineExtras
    #---------------------------------------------------------------------------
    
    def zipPull(self, targets, *keys):
        return self._blockFromThread(self.stpmultiengine.zipPull, targets, *keys)
    
    def zipPullAll(self, *keys):
        return self.zipPull('all', *keys)
    
    def run(self, targets, fname):
        return self._blockFromThread(self.stpmultiengine.run, targets, fnamekeys)
    
    def runAll(self, fname):
        return self.run('all', fname)


components.registerAdapter(FullBlockingMultiEngineClient,
            IFullSynchronousTwoPhaseMultiEngine, IFullBlockingMultiEngineClient)


#-------------------------------------------------------------------------------
# ISynchronousMultiEngine -> IFullBlockingMultiEngineClient adaptor
#-------------------------------------------------------------------------------

def mainClientAdaptor(smultiengine):
    client = me.IFullTwoPhaseMultiEngine(smultiengine)
    client = me.IFullSynchronousTwoPhaseMultiEngine(client)
    client = IFullBlockingMultiEngineClient(client)
    return client

components.registerAdapter(mainClientAdaptor,
            me.ISynchronousMultiEngine, IFullBlockingMultiEngineClient)

#-------------------------------------------------------------------------------
# ISynchronousMultiEngine -> IFullSynchronousTwoPhaseMultiEngine adaptor
#-------------------------------------------------------------------------------

def mainAsynClientAdaptor(smultiengine):
    client = me.IFullTwoPhaseMultiEngine(smultiengine)
    client = me.IFullSynchronousTwoPhaseMultiEngine(client)
    return client

components.registerAdapter(mainAsynClientAdaptor,
            me.ISynchronousMultiEngine, me.IFullSynchronousTwoPhaseMultiEngine)




