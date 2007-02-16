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

import cPickle as pickle

from twisted.internet import reactor
from twisted.python import components
from twisted.python.failure import Failure
from twisted.spread import pb
from zope.interface import Interface, implements

from IPython.ColorANSI import TermColors

import ipython1.kernel.pbconfig
from ipython1.kernel.multiengine import MultiEngine, IMultiEngine
from ipython1.kernel.blockon import blockOn
from ipython1.kernel.util import gatherBoth
from ipython1.kernel.map import Map
from ipython1.kernel.parallelfunction import ParallelFunction

#-------------------------------------------------------------------------------
# ConnectingMultiEngineClient
#-------------------------------------------------------------------------------

class ConnectingMultiEngineClient(object):
    """IMultiEngine Implementer."""
    
    def __init__(self, addr):
        self.addr = addr
        self.multiengine = None
        self.block = False
        self.connected = False
                
    def _blockOrNot(self, d):
        if self.block:
            return self.blockOn(d)
        else:
            return d
           
    def blockOn(self, d):
        return blockOn(d)
            
    #---------------------------------------------------------------------------
    # Methods for subclasses to override
    #---------------------------------------------------------------------------
            
    def connect(self):
        """Create self.multiengine and set self.connected to True."""
        pass
            
    #---------------------------------------------------------------------------
    # Interface methods
    #---------------------------------------------------------------------------

    def execute(self, targets, lines):
        self.connect()
        d = self.multiengine.execute(targets, lines)
        return self._blockOrNot(d)
        
    def executeAll(self, lines):
        return self.execute('all', lines)
        
    def push(self, targets, **namespace):
        self.connect()
        d = self.multiengine.push(targets, **namespace)
        return self._blockOrNot(d)
        
    def pushAll(self, **namespace):
        return self.push('all', **namespace)
        
    def pull(self, targets, *keys):
        self.connect()
        d = self.multiengine.pull(targets, *keys)
        return self._blockOrNot(d)

    def pullAll(self, *keys):
        return self.pull('all', *keys)
    
    def getResult(self, targets, i=None):
        self.connect()
        d = self.multiengine.getResult(targets, i)
        return self._blockOrNot(d)     
    
    def getResultAll(self, i=None):
        return self.getResult('all', i)
    
    def reset(self, targets):
        self.connect()
        d = self.multiengine.reset(targets)
        return self._blockOrNot(d)
    
    def resetAll(self):
        return self.reset('all')
    
    def keys(self, targets):
        self.connect()
        d = self.multiengine.keys(targets)
        return self._blockOrNot(d)
    
    def keysAll(self):
        return self.keys('all')
    
    def kill(self, targets, controller=False):
        self.connect()
        d = self.multiengine.kill(targets, controller)
        return self._blockOrNot(d)
        
    def killAll(self, controller=False):
        return self.kill('all', controller)
    
    def pushSerialized(self, targets, **namespace):
        self.connect()
        d = self.multiengine.pushSerialized(targets, **namespace)
        return self._blockOrNot(d)
    
    def pushSerializedAll(self, **namespace):
        return self.pushSerialized('all', **namespace)
    
    def pullSerialized(self, targets, *keys):
        self.connect()
        d = self.multiengine.pullSerialized(targets, *keys)
        return self._blockOrNot(d)
    
    def pullSerializedAll(self, *keys):
        return self.pullSerialized('all', *keys)
    
    def clearQueue(self, targets):
        self.connect()
        d = self.multiengine.clearQueue(targets)
        return self._blockOrNot(d)
    
    def clearQueueAll(self):
        return self.clearQueue('all')
    
    def queueStatus(self, targets):
        self.connect()
        d = self.multiengine.queueStatus(targets)
        return self._blockOrNot(d)
    
    def queueStatusAll(self):
        return self.queueStatus('all')
        
    def getIDs(self):
        self.connect()
        d = self.multiengine.getIDs()
        return self._blockOrNot(d)
    
    def verifyTargets(self, targets):
        self.connect()
        d = self.multiengine.verifyTargets(targets)
        return self._blockOrNot(d)
        
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        self.connect()
        d = self.multiengine.scatter(targets, key, seq, style, flatten)
        return self._blockOrNot(d)
    
    def scatterAll(self, key, seq, style='basic', flatten=False):
        return self.scatter('all', key, seq, style, flatten)
        
    def gather(self, targets, key, style='basic'):
        self.connect()
        d = self.multiengine.gather(targets, key, style)
        return self._blockOrNot(d)
        
    def gatherAll(self, key, style='basic'):
        return self.gather('all', key, style)

#-------------------------------------------------------------------------------
# InteractiveMultiEngineClient
#-------------------------------------------------------------------------------    

class InteractiveMultiEngineClient(ConnectingMultiEngineClient):
        
    #---------------------------------------------------------------------------
    # Interactive Extensions:
    #
    # ipull/ipullAll
    # iexecute/iexecuteAll
    # igetResult/igetResultAll
    # iqueueStatus/iqueueStatusAll
    # activate
    # run/runAll
    # map/mapAll
    # parallelize/parallelizeAll
    # __len__
    # __setitem__
    # __getitem__
    
    #---------------------------------------------------------------------------
        
    def _transformPullResult(self, pushResult, multitargets, lenKeys):
        if not multitargets:
            result = pushResult[0]
        elif lenKeys > 1:
            result = zip(*pushResult)
        elif lenKeys is 1:
            result = tuple(pushResult)
        return result
        
    def ipull(self, targets, *keys):
        self.connect()
        d = self.multiengine.pull(targets, *keys)
        multitargets = not isinstance(targets, int) and len(targets) > 1
        d.addCallback(self._transformPullResult, multitargets, len(keys))
        return self._blockOrNot(d)
    
    def ipullAll(self, *keys):
        return self.ipull('all', *keys)
        
    def _printResult(self, result):
        if len(result) == 0:
            result = [result]
            
        blue = TermColors.Blue
        normal = TermColors.Normal
        red = TermColors.Red
        green = TermColors.Green
        for cmd in result:
            if isinstance(cmd, Failure):
                print cmd
            else:
                target = cmd['id']
                cmd_num = cmd['commandIndex']
                cmd_stdin = cmd['stdin']
                cmd_stdout = cmd['stdout']
                cmd_stderr = cmd['stderr']
                print "%s[%s:%i]%s In [%i]:%s %s" % \
                    (green, self.addr[0], target,
                    blue, cmd_num, normal, cmd_stdin)
                if cmd_stdout:
                    print "%s[%s:%i]%s Out[%i]:%s %s" % \
                        (green, self.addr[0], target,
                        red, cmd_num, normal, cmd_stdout)
                if cmd_stderr:
                    print "%s[%s:%i]%s Err[%i]:\n%s %s" % \
                        (green, self.addr[0], target,
                        red, cmd_num, normal, cmd_stderr)
        return None
        
    def iexecute(self, targets, lines):
        self.connect()
        d = self.multiengine.execute(targets, lines)
        d.addCallback(self._printResult)
        return self._blockOrNot(d)
        
    def iexecuteAll(self, lines):
        return self.iexecute('all', lines)
        
    def igetResult(self, targets, i=None):
        self.connect()
        d = self.multiengine.getResult(targets, i)
        d.addCallback(self._printResult)
        return self._blockOrNot(d)   
    
    def igetResultAll(self, i=None):
        return self.igetResult('all', i)
    
    def _printQueueStatus(self, status):
        for e in status:
            print "Engine: ", e[0]
            print "    Pending: ", e[1]['pending']
            for q in e[1]['queue']:
                print "    Command: ", q
            
    def iqueueStatus(self, targets):
        self.connect()
        d = self.multiengine.queueStatus(targets)
        d.addCallback(self._printQueueStatus)
        return self._blockOrNot(d)
    
    def iqueueStatusAll(self):
        return self.iqueueStatus('all')
        
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
            
    def run(self, targets, fname):
        """Run a .py file on engine(s).
        
        This reads a local .py file named fname and sends it to be 
        executed on remote engines.  It is executed in the user's
        namespace.  This is intended to function like IPython's run
        magic, but its implementation doesn't work quite right.  But
        for simple files it should work.  
        
        :Parameters:
         - `targets`: The engine id(s) to run on. Targets can be 
           an int, list of ints, or the string 'all' to indicate all 
           available engines.  To see the current ids available on a 
           controller use `getIDs()`.
         - `fname`: The filename to run.
         
        :return: ``True`` or ``False`` to indicate success or failure.    
        """
        fileobj = open(fname,'r')
        source = fileobj.read()
        print source
        fileobj.close()
        # if the compilation blows, we get a local error right away
        code = compile(source,fname,'exec')
        
        # Now run the code
        return self.execute(targets, source)
        
    def runAll(self, fname):
        """Run a .py file on all engines.
        
        See the docstring for `run` for more details.
        """
        return self.run('all', fname)
        
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
        if isinstance(id, slice):
            return InteractiveMultiEngineClientView(self, id)
        elif isinstance(id, int):
            return EngineProxy(self, id)
        elif isinstance(id, str):
            self.connect()
            return self.pull('all', *(id,))
        else:
            raise TypeError("__getitem__ only takes strs, ints, and slices")
            
    def __len__(self):
        """Return the number of available engines."""
        saveBlock = self.block
        self.block = False
        d = self.getIDs()
        d.addCallback(len)
        self.block = saveBlock
        return self._blockOrNot(d)
        
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
        d1 = self.scatter(targets, '_ipython_map_seq', seq, style)
        d2 = self.execute(targets, sourceToRun)
        d3 = self.gather(targets, '_ipython_map_seq_result', style)
        d = gatherBoth([d1 ,d2, d3], fireOnOneErrback=1, consumeErrors=1)
        d.addCallback(lambda r: r[2])
        self.block = saveBlock
        return self._blockOrNot(d)

            
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
        
        if targets == 'all':
            rcview = self
        elif isinstance(targets, int):
            rcview = InteractiveMultiEngineClientView(self, [targets])
        elif isinstance(targets, (list, tuple)):
            rcview = InteractiveMultiEngineClientView(self, targets)
        return ParallelFunction(functionName, rcview)
        
    def parallelizeAll(self, functionName):
        """Build a `ParallelFunction` that operates on all engines.
        
        See the docstring for `parallelize` for more details.
        """
        return self.parallelize('all', functionName)
        

#-------------------------------------------------------------------------------
# InteractiveMultiEngineClient
#-------------------------------------------------------------------------------

class InteractiveMultiEngineClientView(object):
    """A subset interface for InteractiveMultiEngineClient.__getitem__"""
    def __init__(self, imec, ids):
        self.imec = imec
        if isinstance(ids, slice):
            self._originalIDs = range(*ids.indices(ids.stop))
        elif isinstance(ids, list):
            self._originalIDs = ids
        else:
            raise TypeError("RemoteControllerView requires slice or list")
        # Make sure these exist as of now
        currentIDs = imec.getIDs()
        for id in self._originalIDs:
            if id not in currentIDs:
                raise Exception("The engine with id %i does not exist" % id)
        self._ids = range(len(self._originalIDs))
        # print self._ids
        # print self._originalIDs
    
    def _getBlock(self): return self.imec.block
    def _setBlock(self, block): self.imec.block = block
    
    block = property(_getBlock, _setBlock, None, None)
    
    #---------------------------------------------------------------------------
    # IMultiEngine Interface methods
    #---------------------------------------------------------------------------
    
    def execute(self, targets, lines):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.imec.execute(actualTargets, lines)
    
    def executeAll(self, lines):
        return self.execute('all', lines, block)
        
    def push(self, targets, *keys,**namespace):
        if keys: namespace.update(utils.extractVarsAbove(*keys))
        actualTargets = self._mapIDsToOriginal(targets)
        return self.imec.push(actualTargets, **namespace)
    
    def pushAll(self, *keys,**namespace):
        if keys: namespace.update(utils.extractVarsAbove(*keys))
        return self.push('all', **namespace)
        
    def pull(self, targets, *keys):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.imec.pull(actualTargets, *keys)
    
    def pullAll(self, *keys):
        r = self.pull('all', *keys)
        if len(self._ids) is 1:
            r = [r]
        return r
        
    def getResult(self, targets, i=None):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.imec.getResult(actualTargets, i)
    
    def getResultAll(self, i=None):
        r = self.getResult('all', i)
        if len(self._ids) is 1:
            r = [r]
        return r
             
    def reset(self, targets):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.imec.reset(actualTargets)
    
    def resetAll(self):
        return self.reset('all')

    def queueStatus(self, targets):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.imec.queueStatus(actualTargets)
    
    def queueStatusAll(self):
        r = self.queueStatus('all')
        if len(self._ids) is 1:
            r = [r]
        return r
        
    def kill(self, targets):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.imec.kill(actualTargets)
    
    def killAll(self):
        return self.kill('all')
                
    def getIDs(self):
        """Return the ids of the Engines as the Controller indexes them."""
        
        return self._originalIDs

    def scatter(self, targets, key, seq, style='basic', flatten=False):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.imec.scatter(actualTargets, key, seq, style, flatten)
    
    def scatterAll(self, key, seq, style='basic', flatten=False):
        return self.scatter('all', key, seq, style, flatten)
        
    def gather(self, targets, key, style='basic'):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.imec.gather(actualTargets, key, style)        
    
    def gatherAll(self, key, style='basic'):
        return self.gather('all', key, style)
                
    #---------------------------------------------------------------------------
    # InteractiveMultiEngineClient methods
    #---------------------------------------------------------------------------
                
    def activate(self):
        try:
            __IPYTHON__.activeController = self
        except NameError:
            print "The IPython Controller magics only work within IPython."
        
    def run(self, targets, fname):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.imec.run(actualTargets, fname)
    
    def runAll(self, fname):
        return self.run('all', fname)
        
    def __setitem__(self, key, value):
        return self.push('all', **{key:value})
            
    def __getitem__(self, id):
        if isinstance(id, slice):
            return RemoteControllerView(self.imec, self._originalIDs[id])
        elif isinstance(id, int):
            return EngineProxy(self.imec, self._originalIDs[id])
        elif isinstance(id, str):
            return self.pull('all',*(id,))
        else:
            raise TypeError("__getitem__ only takes strs, ints, and slices")
        
    def map(self, targets, functionSource, seq, style='basic'):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.imec.map(actualTargets, functionSource, seq, style)
    
    def mapAll(self, functionSource, seq, style='basic'):
        return self.map('all', functionSource, seq, style)
    
    def parallelize(self, targets, functionName):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.imec.parallelize(actualTargets, functionName)
    
    def parallelizeAll(self, functionName):
        return self.parallelize('all', functionName)
        
    def __len__(self):
        return self.imec.blockOn(self.imec.getIDs())
        
    #---------------------------------------------------------------------------
    # Methods specific to a RemoteControllerView
    #---------------------------------------------------------------------------
        
    def getMappedIDs(self):
        """Return the ids that current operations will succeed on."""
        return self._ids
        
    def _mapIDsToOriginal(self, ids):
        if ids == 'all':
            return self._originalIDs
        elif isinstance(ids, int) and ids in self._ids:
            return self._originalIDs[ids]
        elif isinstance(ids, (list, tuple)):
            return [self._originalIDs[i] for i in ids]
        else:
            raise TypeError("targets/ids must be int, list or tuple")
    
    
#-------------------------------------------------------------------------------
# EngineProxy
#-------------------------------------------------------------------------------
    
class EngineProxy(object):
    """A proxy for an Engine that goes through a RemoteController.

    The user won't ever create these directly.  Instead, the actual
    RemoteController class does that when a particular Engine is indexed.
    """

    def __init__(self, imec, id):
        self.id = id
        self.imec = imec
    
    def execute(self, strings, block=None):
        return self.imec.execute(self.id, strings, block=block)
    
    def push(self, *keys,**namespace):
        if keys: namespace.update(utils.extractVarsAbove(*keys))
        return self.imec.push(self.id, **namespace)
    
    def pull(self, *keys):
        return self.imec.pull(self.id, *keys)

    def getResult(self, i=None):
        return self.imec.getResult(self.id, i)
    
    def status(self):
        return self.imec.status(self.id)
    
    def reset(self):
        return self.imec.reset(self.id)
    
    def kill(self):
        return self.imec.kill(self.id)

    def __setitem__(self, key, value):
        return self.push(**{key:value})
        
    def __getitem__(self, key):
        return self.pull(*(key,))