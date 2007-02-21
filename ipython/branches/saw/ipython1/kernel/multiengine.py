# encoding: utf-8
# -*- test-case-name: ipython1.test.test_multiengine -*-
"""Adapt the IPython Controller to MultiEngine.

This module provides classes that adapt a ControllerService for clients
that wish to have explicit access to each registered engine.  It is 
designed for interactive clients.

The classes here are exposed to the network in the files:

 * multienginevanilla.py
 * multienginepb.py
 
Eventually, these should be named multiengine*.py.
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

from new import instancemethod
from twisted.application import service
from twisted.internet import defer, reactor
from twisted.python import log, components, failure
from zope.interface import Interface, implements, Attribute

from ipython1.kernel.serialized import Serialized
from ipython1.kernel.util import gatherBoth
from ipython1.kernel import map as Map
from ipython1.kernel import error
from ipython1.kernel.controllerservice import \
    ControllerAdapterBase, \
    ControllerService
from ipython1.kernel.pendingdeferred import PendingDeferredAdapter, TwoPhase

#-------------------------------------------------------------------------------
# Interfaces for the MultiEngine representation of a controller
#-------------------------------------------------------------------------------

class IEngineMultiplexer(Interface):
    """Interface to multiple objects implementing IEngineCore/Serialized/Queued.
    
    This class simply acts as a multiplexer of Engines.
    Thus the methods here are jut like those in the IEngine*
    interfaces, but with an extra argument: targets.  The targets argument
    can have the following forms:
    
    targets = 10            # Engines are indexed by ints
    targets = [0,1,2,3]     # A list of ints
    targets = 'all'         # A string to indicate all targets
    
    All IEngineMultiplexer multiplexer methods must return a Deferred to a list 
    with length equal to the number of targets.  The elements of the list will 
    correspond to the return of the corresponding IEngine method.
    
    Failures are aggressive:  if the action fails for any target, the overall
    action will fail immediately with that Failure.
    
    :Exceptions:
        - `InvalidEngineID`: If the targets argument is bad in any way.
    """
        
    #---------------------------------------------------------------------------
    # Mutiplexed methods
    #---------------------------------------------------------------------------
     
    def execute(targets, lines):
        """Execute lines of Python code on target."""
    
    def executeAll(lines):
        """Execute on all targets."""
        
    def push(targets, **namespace):
        """Push dict namespace into the user's namespace on targets."""
        
    def pushAll(**namespace):
        """Push to all targets."""
        
    def pull(targets, *keys):
        """Pull values out of the user's namespace on targets by keys."""
        
    def pullAll(*keys):
        """Pull from all targets."""
                
    def getResult(targets, i=None):
        """Get the result tuple for command i from targets."""
        
    def getResultAll(i=None):
        """Get the result tuple for command i from all targets."""
        
    def reset(targets):
        """Reset targets.
        
        This clears the users namespace of the Engines, but won't cause
        modules to be reloaded.
        """
        
    def resetAll():
        """Reset all targets."""
        
    def keys(targets):
        """Get variable names on targets."""
        
    def keysAll():
        """Get variable names on all targets."""
        
    def kill(targets, controller=False):
        """Kill the targets Engines and possibly the controller."""
        
    def killAll(controller=False):
        """Kill all the Engines and possibly the controller."""
        
    def pushSerialized(targets, **namespace):
        """Push a namespace of Serialized objects to targets."""
        
    def pushSerializedAll(**namespace):
        """Push Serialized to all targets."""
        
    def pullSerialized(targets, *keys):
        """Pull Serialized objects by keys from targets."""
        
    def pullSerializedAll(*keys):
        """Pull Serialized from all targets."""
        
    def clearQueue(targets):
        """Clear the queue of pending command for targets."""
        
    def clearQueueAll():
        """Clear the queue of pending commands for all targets."""
        
    def queueStatus(targets):
        """Get the status of the queue on the targets."""
        
    def queueStatusAll():
        """Get the status of all the queues."""
        
class IEngineCoordinator(Interface):
    """Methods that work on multiple engines explicitly.
    
    :Exceptions:
        - `InvalidEngineID`: If the targets argument is bad in any way.
    """
        
    #---------------------------------------------------------------------------
    # Coordinated methods
    #---------------------------------------------------------------------------
         
    def scatter(targets, key, seq, style='basic', flatten=False):
        """Partition and distribute a sequence to targets."""
    
    def scatterAll(key, seq, style='basic', flatten=False):
        """Scatter to all targets."""
    
    def gather(targets, key, style='basic'):
        """Gather object key from targets."""
    
    def gatherAll(key, style='basic'):
        """Gather from all targets."""
        
        
class IMultiEngine(IEngineMultiplexer, 
                   IEngineCoordinator):
    """A controller that exposes an explicit interface to all of its engines.
    
    This is the primary inteface for interactive usage.
    """

    def getIDs():
        """Return list of currently registered ids."""

    def verifyTargets(self, targets):
        """Is targets a list of active engine ids."""
        
        
#-------------------------------------------------------------------------------
# Implementation of the ControllerService
#-------------------------------------------------------------------------------
        
class MultiEngine(ControllerAdapterBase):
    """The representation of a ControllerService as a IMultiEngine.
    
    Although it is not implemented currently, this class would be where a
    client/notification API is implemented.  It could inherit from something
    like results.NotifierParent and then use the notify method to send
    notifications.
    """
    
    implements(IMultiEngine)
    
    def __init(self, controller):
        ControllerAdapterBase.__init__(self, controller)

    #---------------------------------------------------------------------------
    # Helper methods
    #---------------------------------------------------------------------------

    def engineList(self, targets):
        """parse a *valid* id list into list of engines"""
        # we could be strict here
        # assert self.verifyTargets(targets), "need valid ids"
        if isinstance(targets, int):
            return [self.engines[targets]]
        elif isinstance(targets, (list, tuple)):
            return map(self.engines.get, targets)
        elif targets == 'all':
            return self.engines.values()
        else:
            return []
    
    #---------------------------------------------------------------------------
    # Override ControllerAdapterBase methods
    # This is only needed to add additional features like notifications to the
    # methods of ControllerAdapterBase
    #---------------------------------------------------------------------------
    
    #---------------------------------------------------------------------------
    # General IMultiEngine methods
    #---------------------------------------------------------------------------
    
    def getIDs(self):
        """Return a list of active engine ids."""
        
        return defer.succeed(self.engines.keys())
    
    def verifyTargets(self, targets):
        """Is targets a valid list of active engines."""
        
        if isinstance(targets, int):
            if targets not in self.engines.keys():
                log.msg("id %i not registered" %targets)
                return False
            else: 
                return True
        elif isinstance(targets, list):
            for id in targets:
                if id not in self.engines.keys():
                    log.msg("id %i not registered" %id)
                    return False
            print 
            return True
        elif targets == 'all':
            return True
        else:
            return False
    
    #---------------------------------------------------------------------------
    # IEngineMultiplexer methods
    #---------------------------------------------------------------------------
        
    def execute(self, targets, lines):
        if len(lines) > 64:
            linestr = lines[:61]+'...'
        else:
            linestr = lines
        log.msg("executing %s on %s" %(linestr, targets))
        engines = self.engineList(targets)
        dList = []
        for e in engines:
            d = e.execute(lines)
            # This would be the place to addCallback to any notification methods
            dList.append(d)
        return gatherBoth(dList, 
                          fireOnOneErrback=1,
                          consumeErrors=1,
                          logErrors=0)
    
    def executeAll(self, lines):
        return self.execute('all', lines)
    
    def push(self, targets, **ns):
        log.msg("pushing to %s" % targets)
        engines = self.engineList(targets)
        dList = []
        for e in engines:
            dList.append(e.push(**ns))
        return gatherBoth(dList, 
                          fireOnOneErrback=1,
                          consumeErrors=1,
                          logErrors=0)
    
    def pushAll(self, **ns):
        return self.push('all', **ns)
        
    def pull(self, targets, *keys):
        log.msg("pulling from %s" % targets)
        engines = self.engineList(targets)
        dList = []
        for e in engines:
            dList.append(e.pull(*keys))
        return gatherBoth(dList, 
                          fireOnOneErrback=1,
                          consumeErrors=1,
                          logErrors=0)
    
    def pullAll(self, *keys):
        return self.pull('all', *keys)
    
    def getResult(self, targets, i=None):
        log.msg("getResult on %s" % targets)
        engines = self.engineList(targets)
        dList = []
        for e in engines:
            dList.append(e.getResult(i))
        return gatherBoth(dList, 
                          fireOnOneErrback=1,
                          consumeErrors=1,
                          logErrors=0)                

    def getResultAll(self, i=None):
        return self.getResult('all', i)
    
    def reset(self, targets):
        log.msg("reseting %s" % targets)
        engines = self.engineList(targets)
        dList = []
        for e in engines:
            dList.append(e.reset())
        return gatherBoth(dList, 
                          fireOnOneErrback=1,
                          consumeErrors=1,
                          logErrors=0)    

    def resetAll(self):
        return self.reset('all')
    
    def keys(self, targets):
        log.msg("getting keys from %s" % targets)
        engines = self.engineList(targets)
        dList = []
        for e in engines:
            dList.append(e.keys())
        return gatherBoth(dList, 
                          fireOnOneErrback=1,
                          consumeErrors=1,
                          logErrors=0)    

    def keysAll(self):
        return self.keys('all')
    
    def kill(self, targets, controller=False):
        log.msg("killing engines %s" % targets)
        if controller: targets = 'all'              # kill all engines if killing controller
        engines = self.engineList(targets)
        dList = []
        for e in engines:
            dList.append(e.kill())
        d = gatherBoth(dList, 
                       fireOnOneErrback=1,
                       consumeErrors=1,
                       logErrors=0)        
        if controller:
            log.msg("Killing controller")
            d.addCallback(lambda _: reactor.callLater(2,0, reactor.stop))
        return d
        
    def killAll(self, controller=False):
        return self.kill('all', controller)
    
    def pushSerialized(self, targets, **namespace):
        log.msg("pushing Serialized to %s" % targets)
        engines = self.engineList(targets)
        dList = []
        for k, v in namespace.iteritems():
            log.msg("Pushed object %s is %f MB" % (k, v.getDataSize()))
        for e in engines:
            dList.append(e.pushSerialized(**namespace))
        return gatherBoth(dList, 
                          fireOnOneErrback=1,
                          consumeErrors=1,
                          logErrors=0)  
                              
    def pushSerializedAll(self, **namespace):
        return self.pushSerialized('all', **namespace)
        
    def pullSerialized(self, targets, *keys):
        log.msg("pulling serialized from %s" % targets)
        engines = self.engineList(targets)
        dList = []
        for e in engines:
            d = e.pullSerialized(*keys)
            d.addCallback(self._logSizes)
            dList.append(d)
        return gatherBoth(dList, 
                          fireOnOneErrback=1,
                          consumeErrors=1,
                          logErrors=0)  
                              
    def _logSizes(self, listOfSerialized):
        if isinstance(listOfSerialized, (list, tuple)):
            for s in listOfSerialized:
                log.msg("Pulled object is %f MB" % s.getDataSize())
        else:
            log.msg("Pulled object is %f MB" % listOfSerialized.getDataSize())
        return listOfSerialized
    
    def pullSerializedAll(self, *keys):
        return self.pullSerialized('all', *keys)
    
    def clearQueue(self, targets):
        log.msg("clearing queue on %s" % targets)
        engines = self.engineList(targets)
        dList = []
        for e in engines:
            dList.append(e.clearQueue())
        return gatherBoth(dList, 
                          fireOnOneErrback=1,
                          consumeErrors=1,
                          logErrors=0)  
                              
    def clearQueueAll(self):
        return self.clearQueue('all')
    
    def queueStatus(self, targets):
        log.msg("getting queue status on %s" % targets)
        engines = self.engineList(targets)
        dList = []
        for e in engines:
            dList.append(e.queueStatus().addCallback(lambda s:(e.id, s)))
        return gatherBoth(dList, 
                          fireOnOneErrback=1,
                          consumeErrors=1,
                          logErrors=0)  
                          
    def queueStatusAll(self):
        return self.queueStatus('all')

    #---------------------------------------------------------------------------
    # IEngineCoordinator methods
    #---------------------------------------------------------------------------

    def scatter(self, targets, key, seq, style='basic', flatten=False):
        log.msg("scattering %s to %s" %(key, targets))
        engines = self.engineList(targets)
        nEngines = len(engines)
    
        mapClass = Map.styles[style]
        mapObject = mapClass()
        dList = []
        for index, engine in enumerate(engines):
            partition = mapObject.getPartition(seq, index, nEngines)
            if flatten and len(partition) == 1:    
                dList.append(engine.push(**{key: partition[0]}))
            else:
                dList.append(engine.push(**{key: partition}))
        return gatherBoth(dList, 
                          fireOnOneErrback=1,
                          consumeErrors=1,
                          logErrors=0)  
                              
    def scatterAll(self, key, seq, style='basic', flatten=False):
        return self.scatter('all', key, seq, style, flatten)
    
    def gather(self, targets, key, style='basic'):
        """gather a distributed object, and reassemble it"""
        log.msg("gathering %s from %s"%(key, targets))
        engines = self.engineList(targets)
        nEngines = len(engines)
            
        dList = []
        for e in engines:
            dList.append(e.pull(key))
    
        mapClass = Map.styles[style]
        mapObject = mapClass()
        d = gatherBoth(dList, 
                       fireOnOneErrback=1,
                       consumeErrors=1,
                       logErrors=0)  
        return d.addCallback(mapObject.joinPartitions)
    
    def gatherAll(self, key, style='basic'):
        return self.gather('all', key, style)


components.registerAdapter(MultiEngine, 
                           ControllerService, 
                           IMultiEngine)


#-------------------------------------------------------------------------------
# Synchronous MultiEngine
#-------------------------------------------------------------------------------

class ISynchronousMultiEngine(Interface):
    pass


class SynchronousMultiEngine(PendingDeferredAdapter):
    
    implements(ISynchronousMultiEngine)
    
    def __init__(self, multiengine):
        self.multiengine = multiengine
        PendingDeferredAdapter.__init__(self)

        # Now apply the TwoPhase wrapper class to all the methods of self.multiengine.
        self.execute = TwoPhase(self, self.multiengine.execute)
        self.push = TwoPhase(self, self.multiengine.push)
        self.pull = TwoPhase(self, self.multiengine.pull)
        self.getResult = TwoPhase(self, self.multiengine.getResult)
        self.reset = TwoPhase(self, self.multiengine.reset)
        self.keys = TwoPhase(self, self.multiengine.keys)
        self.kill = TwoPhase(self, self.multiengine.kill)
        self.pushSerialized = TwoPhase(self, self.multiengine.pushSerialized)
        self.pullSerialized = TwoPhase(self, self.multiengine.pullSerialized)
        self.clearQueue = TwoPhase(self, self.multiengine.clearQueue)
        self.queueStatus = TwoPhase(self, self.multiengine.queueStatus)
        self.scatter = TwoPhase(self, self.multiengine.scatter)
        self.gather = TwoPhase(self, self.multiengine.gather)
                
    #---------------------------------------------------------------------------
    # IMultiEngine methods
    #---------------------------------------------------------------------------

    def getIDs(self):
        return self.multiengine.getIDs()

    def verifyTargets(self, targets):
        return self.multiengine.verifyTargets(targets)

components.registerAdapter(SynchronousMultiEngine, IMultiEngine, ISynchronousMultiEngine)