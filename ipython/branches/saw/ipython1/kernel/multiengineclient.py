# encoding: utf-8
# -*- test-case-name: ipython1.test.test_multiengineclient -*-
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

from twisted.internet import reactor
from twisted.python import components
from twisted.python.failure import Failure
from twisted.spread import pb
from zope.interface import Interface, implements, Attribute

from IPython.ColorANSI import TermColors

from ipython1.kernel import error
from ipython1.kernel.parallelfunction import ParallelFunction


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
        
        If the original result is result, adding a callback will cause
        f(result, *args, **kwargs) to be returned instead.  If multiple
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
        and see if the result is ready.  If the action trigger an exception
        raise it and record it.  This method records the result/exception once it is 
        retrieved.  Calling getResult() again will get this cached result or will
        re-raise the exception.
        
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
            result = self.client._getPendingResult(self.resultID, block)
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
                target = cmd['id']
                cmd_num = cmd['commandIndex']
                cmd_stdin = cmd['stdin']
                cmd_stdout = cmd['stdout']
                cmd_stderr = cmd['stderr']
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
        
    #---------------------------------------------------------------------------
    # Interactive Extensions:
    #
    # activate
    # run/runAll
    # map/mapAll
    # parallelize/parallelizeAll
    # __len__
    # __setitem__
    # __getitem__
    
    #---------------------------------------------------------------------------
    
    _magicTargets = 'all'
    
    def _setMagicTargets(self, targets):
        self._magicTargets = targets
        
    def _getMagicTargets(self):
        return self._magicTargets
    
    magicTargets = property(_getMagicTargets, _setMagicTargets, None, None)
            
    def _transformPullResult(self, pushResult, multitargets, lenKeys):
        if not multitargets:
            result = pushResult[0]
        elif lenKeys > 1:
            result = zip(*pushResult)
        elif lenKeys is 1:
            result = list(pushResult)
        return result
        
    def zipPull(self, targets, *keys):
        result = self.pull(targets, *keys)
        multitargets = not isinstance(targets, int) and len(targets) > 1
        lenKeys = len(keys)
        if self.block:
            result = self._transformPullResult(result, multitargets, lenKeys)
        else:
            result.addCallback(self._transformPullResult, multitargets, lenKeys)
        return result
            
    def zipPullAll(self, *keys):
        return self.zipPull('all', *keys)
                    
    def activate(self):
        """Make this `RemoteController` active for parallel magic commands.
        
        IPython has a magic command syntax to work with `RemoteController` objects.
        In a given IPython session there is a single active cluster.  While
        there can be many `RemoteController` created and used by the user, 
        there is only one active one.  The active `RemoteController` is used whenever 
        the magic commands %px, %pn, and %autopx are used.
        
        The activate() method is called on a given `RemoteController` to make it 
        active.  Once this has been done, the magic commands can be used.
        
        Examples
        
        >>> rc = RemoteController(('localhost',10000))
        >>> rc.activate()
        >>> %px a = 5       # Same as executeAll('a = 5')        
        >>> %pn 0 b = 10    # Same as execute(0,'b=10')
        >>> %autopx         # Now every command is sent to execute()
        ...
        >>> %autopx         # The second time it toggles autoparallel mode off
        """
        
        try:
            __IPYTHON__.activeController = self
        except NameError:
            print "The IPython Controller magics only work within IPython."
            
    def run(self, targets, fname, block=None):
        """Run a .py file on targets."""
        fileobj = open(fname,'r')
        source = fileobj.read()
        fileobj.close()
        # if the compilation blows, we get a local error right away
        code = compile(source,fname,'exec')
        
        # Now run the code
        return self.execute(targets, source, block)
        
    def runAll(self, fname, block=None):
        """Run a .py file on all engines.
        
        See the docstring for `run` for more details.
        """
        return self.run('all', fname, block)
        
    def __setitem__(self, key, value):
        """Add a dictionary interface to `RemoteController`.
        
        This functions as a shorthand for `push`.
        
        Examples:
        
        >>> rc = RemoteController(('localhost',10000))
        >>> rc['a'] = 10                      # Same as rc.pushAll(a=10)
        
        :Parameters:
         - `key`: What to call the remote object.
         - `value`: The local Python object to push.
        """
        return self.push('all', **{key:value})
    
    def __getitem__(self, id):
        """Add list and dict interface to `RemoteController`.
        
        This lets you index a `RemoteController` object as either a list
        or a dictionary.  
        
        The dictionary interface is shorthand for pull:
        
        >>> rc = RemoteController(('localhost',10000))
        >>> rc['a']                     # Same as rc.pullAll('a')
        (10, 10, 10, 10)
        
        When indexed as a list, the rc object returns an `EngineProxy`
        or RemoteControllerView object.  These objects have the same
        interface as a RemoteController object, but work only on a single
        engine:
        
        >>> engine0 = rc[0]               # Create an interface to engine 0
        >>> engine0.execute('a=math.pi')  # Same as rc.execute(0,'a=math.pi')
        
        Or a subset of engines:
        
        >>> subset = rc[0:4]              # Subset is a RemoteControllerView
        >>> subset.executeAll('c=30')     # Same as rc.execute(range(0,4),'c=30')
        
        You can use this notation in combination with the dictionary notation 
        to do things like:
        
        >>> rc[0]['a'] = 30
        >>> localresult = rc[5]['result']
        
        :Parameters:
         - `id`: A string representing the key.
        """
        if isinstance(id, str):
            return self.pull('all', *(id,))
        else:
            raise TypeError("__getitem__ only takes strs")
            
    def __len__(self):
        """Return the number of available engines."""
        return len(self.getIDs())
        
    def map(self, targets, functionSource, seq, style='basic'):
        """A parallelized version of Python's builtin map.
        
        This function implements the following pattern:
        1. The sequence seq is scattered to the given targets.
        2. map(functionSource, seq) is called on each engine.
        3. The resulting sequences are gathered back to the local machine.
                
        Example:
        
        >>> map('lambda x: x*x', range(10000))
        [0,2,4,9,25,36,...]

        :Parameters:
         - `targets`: The engine id(s) to map on. Targets can be 
           an int, list of ints, or the string 'all' to indicate all 
           available engines.  To see the current ids available on a 
           controller use `getIDs()`.
         - `functionSource`: A string representation of a callable that is
           defined on the engines.
         - `seq`: The local sequence to be scattered.
         - `style`: The style of `scatter`/`gather` to use.  So far only ``basic``
           is implemented.
           
        :return: A list of len(seq) with functionSource called on each element
            of ``seq``.
        """
        saveBlock = self.block
        self.block = False
        sourceToRun = \
            '_ipython_map_seq_result = map(%s, _ipython_map_seq)' % \
            functionSource        
        pd1 = self.scatter(targets, '_ipython_map_seq', seq, style)
        print pd1.getResult()
        pd2 = self.execute(targets, sourceToRun)
        print pd2.getResult()
        pd3 = self.gather(targets, '_ipython_map_seq_result', style)
        self.block = saveBlock
        return pd3.getResult()
            
    def mapAll(self, functionSource, seq, style='basic'):
        """Parallel map on all engines.
        
        See the docstring for `map` for more details.
        """
        return self.map('all', functionSource, seq, style)

    def parallelize(self, targets, functionName):
        """Build a `ParallelFunction` object for functionName on engines.
        
        The returned object will implement a parallel version of functionName
        that takes a local sequence as its only argument and calls (in 
        paralle) functionName on each element of that sequence.
        
        Examples:
        
        >>> rc = RemoteController(('localhost',10000))
        >>> psin = rc.parallelize('all','lambda x:x*x')
        >>> psin(range(10000))
        [0,2,4,9,25,36,...]
        
        :Parameters:
         - `targets`: The engine id(s) to use. Targets can be 
           an int, list of ints, or the string 'all' to indicate all 
           available engines.  To see the current ids available on a 
           controller use `getIDs()`.
         - `functionName`: The string representation of a Python callable
           that is defined on the engines.  This functions will be parallelized.
           
        :return:  A `ParallelFunction` object for targets.
        """
        
        return ParallelFunction(targets, functionName, self)
        
    def parallelizeAll(self, functionName):
        """Build a `ParallelFunction` that operates on all engines.
        
        See the docstring for `parallelize` for more details.
        """
        return self.parallelize('all', functionName)
