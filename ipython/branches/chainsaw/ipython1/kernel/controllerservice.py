# -*- test-case-name: ipython1.test.test_controllerservice -*-
"""A Twisted Service for the IPython Controller.

The IPython Controller:

 * Listens for Engines to connect and then manages those Engines.
 * Listens for clients and passes commands from client to the Engines.
 * Exposes an asynchronous interfaces to the Engines which themselves can block.
 * Acts as a gateway to the Engines.
"""

#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

from new import instancemethod
from twisted.application import service
from twisted.internet import defer
from twisted.python import log
from zope.interface import Interface, implements

from ipython1.kernel.engineservice import IEngineComplete
from ipython1.kernel.serialized import Serialized
from ipython1.kernel.util import gatherBoth
from ipython1.kernel import map as Map
from ipython1.kernel import results

#-------------------------------------------------------------------------------
# Interfaces for the Controller
#-------------------------------------------------------------------------------


class IRemoteController(Interface):
    """The Interface a ControllerService exposes to an EngineService."""
    
    def registerEngine(remoteEngine, id):
        """Register new remote engine.
        
        remoteEngine: an implementer of IEngineComplete
        id: requested id
        
        Returns the actual id granted.
        """
    
    def unregisterEngine(id):
        """Handle a disconnecting engine."""
    
    def registerSerializationTypes(self, *serialTypes):
        """Register the set of allowed subclasses of Serialized."""
    

class IMultiEngine(Interface):
    """Interface to multiple objects implementing IEngineComplete.
    
    For the most part this class simply acts as a multiplexer of Engines.
    Thus most of the methods here are jut like those in the IEngine*
    interfaces, but with an extra argument: targets.  The targets argument
    can have the following forms:
    
    targets = 10            # Engines are indexed by ints
    targets = [0,1,2,3]     # A list of ints
    targets = 'all'         # A string to indicate all targets
    
    All IMultiEngine methods must return a Deferred to a list with length 
    equal to the number of targets, except for verifyTargets.
    """
    
    #---------------------------------------------------------------------------
    # Non multiplexed methods
    #---------------------------------------------------------------------------
    
    def verifyTargets(targets):
        """Verify if targets is callable id list, id, or string 'all'"""
    
    def getIDs():
        """Return list of currently registered ids."""
    
    def scatter(targets, key, seq, style='basic', flatten=False):
        """Partition and distribute a sequence to targets."""
    
    def scatterAll(key, seq, style='basic', flatten=False):
        """Scatter to all targets."""
    
    def gather(targets, key, style='basic'):
        """Gather object key from targets."""
    
    def gatherAll(key, style='basic'):
        """Gather from all targets."""
        
    #---------------------------------------------------------------------------
    # Mutiplexed IEngine methos
    #---------------------------------------------------------------------------
     
    def execute(targets, lines):
        """"""
    
    def executeAll(lines):
        """"""
        
    def push(targets, **namespace):
        """"""
        
    def pushAll(**namespace):
        """"""
        
    def pull(targets, *keys):
        """"""
        
    def pullAll(*keys):
        """"""
    
    def pullNamespace(targets, *keys):
        """"""
    
    def pullNamespaceAll(*keys):
        """"""
        
    def getResult(targets, i=None):
        """"""
        
    def getResultAll(i=None):
        """"""
        
    def reset(targets):
        """"""
        
    def resetAll():
        """"""
        
    def status(targets):
        """"""
        
    def statusAll():
        """"""
        
    def kill(targets):
        """"""
        
    def killAll():
        """"""
        
    def pushSerialized(targets, **namespace):
        """"""
        
    def pushSerializedAll(**namespace):
        """"""
        
    def pullSerialized(targets, *keys):
        """"""
        
    def pullSerializedAll(*keys):
        """"""
        
    def clearQueue(targets):
        """"""
        
    def clearQueueAll():
        """"""
        
        
class IController(IRemoteController, IMultiEngine, results.INotifierParent):
    """The Controller is an IRemoteController, IMultiEngine & INotifierParent."""
    
    pass 


#-------------------------------------------------------------------------------
# Implementation of the ControllerService
#-------------------------------------------------------------------------------


def addAllMethods(obj, interface=IMultiEngine):
    """Dynamically generate the fooAll methods in IController."""
    for m in interface:
        # print m
        # print hasattr(obj, m),not hasattr(obj, m+'All')
        if m+'All' in interface and hasattr(obj, m) and not hasattr(obj, m+'All'):
            # methods that have 'All' suffix in interface and regular in obj
            M = interface[m]
            MA = interface[m+'All']
            defs = """
def allMethod(self, %s):
    '''%s'''
    return self.%s('all'%s)
""" %(MA.getSignatureString()[1:-1], MA.getDoc(), m, M.getSignatureString()[8:-1])
            exec defs
            setattr(obj, m+'All', instancemethod(allMethod, obj, obj.__class__))
            del allMethod
    return obj


class ControllerService(service.Service, results.NotifierParent):
    """A Controller represented as a Twisted Service.
    """
    
    implements(IController)
    
    def __init__(self, maxEngines=255, saveIDs=False):
        self.saveIDs = saveIDs
        self.engines = {}
        self.availableIDs = range(maxEngines,-1,-1)#[255,...,0]
        self.serialTypes = ()
        self.setAutoMethods()
    
    def setAutoMethods(self):
        """
        Automatically generates methods from IMultiEngine
        
        what they look like:
        
        def <fname>(self, targets, *args, **kwargs):
            log.msg("<fname> on %s" %(targets))
            engines = self.engineList(targets)
            l = []
            for e in engines:
                l.append(e.<fname>(*args, **kwargs))
            d = gatherBoth(l)
        """
        for m in IMultiEngine:
            IM = IMultiEngine[m]
            #first setup non-All methods
            if callable(IM) and m[-3:] != 'All'\
                    and getattr(self, m, None) is None:
                #only work on methods, not attributes, and only on methods
                #not already defined
                eSig = IEngineComplete[m].getSignatureString()
                defs = """
def autoMethod(self, %s:
    '''%s'''
    log.msg('%s on %%s' %%targets)
    engines = self.engineList(targets)
    l = []
    for e in engines:
        l.append(e.%s%s)
    return gatherBoth(l)
"""%(IM.getSignatureString()[1:], IM.getDoc(), IM.getName(), m, eSig)
                try:
                    exec(defs)
                    setattr(self, m, instancemethod(autoMethod, self, self.__class__))
                    #del autoMethod
                except:
                    log.msg("failed autogen method %s" %m)
                    raise
        addAllMethods(self)
    
    #---------------------------------------------------------------------------
    # IRemoteController methods
    #---------------------------------------------------------------------------
    
    def registerEngine(self, remoteEngine, id=None):
        """register new engine connection"""
        for base in IEngineComplete.getBases():
            assert(base.providedBy(remoteEngine))
        
        desiredID = id
        if desiredID in self.engines.keys():
            desiredID = None
            
        if desiredID in self.availableIDs:
            remoteEngine.id = desiredID
            self.availableIDs.remove(desiredID)
        else:
            remoteEngine.id = self.availableIDs.pop()
            
        remoteEngine.service = self
        self.engines[remoteEngine.id] = remoteEngine
        msg = "registered engine: " + repr(remoteEngine.id)
        log.msg(msg)
        self.notify((remoteEngine.id, -1, msg, '', ''))
        return remoteEngine.id
    
    def unregisterEngine(self, id):
        """eliminate remote engine object"""
        msg = "unregistered engine %r" %id
        log.msg(msg)
        del self.engines[id]
        if not self.saveIDs:
            self.availableIDs.append(id)
            # Sort to assign lower ids first
            self.availableIDs.sort(reverse=True) 
        else:
            log.msg("preserving id %i" %id)
        self.notify((id, -1, msg, '', ''))
    
    def registerSerializationTypes(self, *serialTypes):
        """Register the set of allowed subclasses of Serialized."""
        self.serialTypes = serialTypes
    
    #ImultiEngine helper methods

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
    # IMultiEngine methods
    #---------------------------------------------------------------------------
    # Only certain methods must be done by hand, the other are dynamically 
    # generated.
    
    def verifyTargets(self, targets):
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
        elif targets is 'all':
            return True
        else:
            return False
    
    def getIDs(self):
        return defer.succeed(self.engines.keys())
    
    def execute(self, targets, lines):        
        if len(lines) > 64:
            linestr = lines[:61]+'...'
        else:
            linestr = lines
        log.msg("executing %s on %s" %(linestr, targets))
        engines = self.engineList(targets)
        l = []
        for e in engines:
            d = e.execute(lines).addCallback(self.notify)
            l.append(d)
        return gatherBoth(l)
    
    def pushSerialized(self, targets, **namespace):
        log.msg("pushing Serialized to %s" % targets)
        engines = self.engineList(targets)
        l = []
        # Call unpack on values that aren't registered as allowed Serialized types
        for k, v in namespace.iteritems():
            if not isinstance(v, self.serialTypes) and isinstance(v, Serialized):
                    log.msg("unpacking serial, ", k)
                    namespace[k] = v.unpack()
        for e in engines:
            l.append(e.pushSerialized(**namespace))
        return gatherBoth(l)
    
    def status(self, targets):
        log.msg("retrieving status of %s" %targets)
        engines = self.engineList(targets)
        l = []
        for e in engines:
            l.append(e.status().addCallback(lambda s:(e.id, s)))
        return gatherBoth(l)
        
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        log.msg("scattering %s to %s" %(key, targets))
        engines = self.engineList(targets)
        nEngines = len(engines)
        
        mapClass = Map.styles[style]
        mapObject = mapClass()
        l = []
        for index, engine in enumerate(engines):
            partition = mapObject.getPartition(seq, index, nEngines)
            if flatten and len(partition) == 1:    
                l.append(engine.push(**{key: partition[0]}))
            else:
                l.append(engine.push(**{key: partition}))
        return gatherBoth(l)
    
    def gather(self, targets, key, style='basic'):
        """gather a distributed object, and reassemble it"""
        log.msg("gathering %s from %s"%(key, targets))
        engines = self.engineList(targets)
        nEngines = len(engines)
                
        l = []
        for e in engines:
            l.append(e.pull(key))
        
        mapClass = Map.styles[style]
        mapObject = mapClass()
        return gatherBoth(l).addCallback(mapObject.joinPartitions)
    
