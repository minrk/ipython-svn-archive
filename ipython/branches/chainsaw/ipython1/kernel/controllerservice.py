# -*- test-case-name: ipython1.test.test_controllerservice -*-
"""A Twisted Service for the Controller

TODO:

- Use subclasses of pb.Error to pass exceptions back to the calling process.
- Deal more carefully with the failure modes of the kernel engine.
- Add an XML-RPC interface
- Add an HTTP interface
- Security!!!!!
"""

#*****************************************************************************
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

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

# Interface for the Controller Service

class IRemoteController(Interface):
    """The Interface the controller exposes to remote engines."""
    
    def registerEngine(remoteEngine, id):
        """register new remote engine"""
    
    def unregisterEngine(id):
        """handle disconnecting engine"""
    
    def registerSerializationTypes(self, *serialTypes):
        """Register the set of allowed subclasses of Serialized."""
    

class IMultiEngine(Interface):
    """interface to multiple objects implementing IEngineComplete.
    
    All IMultiEngine methods must return a Deferred to alist with length 
    equal to the number of targets, except for verifyTargets.
    """
    
    def verifyTargets(targets):
        """verify if targets is callable id list, id, or string 'all'"""
    
    def getIDs():
        """return list of currently registered ids."""
    
    def scatter(targets, key, seq, style='basic', flatten=False):
        """partition and distribute a sequence"""
    
    def scatterAll(key, seq, style='basic', flatten=False):
        """"""
    
    def gather(targets, key, style='basic'):
        """gather object as distributed by scatter"""
    
    def gatherAll(key, style='basic'):
        """"""
    #IRemoteEngine multiplexer methods
    def pushSerialized(targets, **namespace):
        """Push a dict of keys and Serialized to the user's namespace."""
    
    def pushSerializedAll(**namespace):
        """Push a dict of keys and Serialized to the user's namespace."""
    
    def pullSerialized(targets, *keys):
        """Pull objects by key form the user's namespace as Serialized."""
    
    def pullSerializedAll(*keys):
        """Pull objects by key form the user's namespace as Serialized."""
    
    #IQueuedEngine multiplexer methods
    def clearQueue(targets):
        """Clears out pending commands in an engine's queue."""
    
    def clearQueueAll():
        """Clears out pending commands in all queues."""
    
    #IEngineCompleteBase multiplexer methods
    def execute(targets, lines):
        """Execute lines of Python code."""
    
    def executeAll(lines):
        """Execute lines of Python code."""
    
    def push(targets, **namespace):
        """Push value into locals namespace with name key."""
    
    def pushAll(**namespace):
        """"""
    
    def pull(targets, *keys):
        """Gets an item out of the self.locals dict by key."""
    
    def pullAll(*keys):
        """"""
    
    def pullNamespace(targets, *keys):
        """Gets a namespace dict from targets by keys."""
    
    def pullNamespaceAll(*keys):
        """"""
    
    def getResult(targets, i=None):
        """Get the stdin/stdout/stderr of command i."""
    
    def getResultAll(i=None):
        """"""
    
    def reset(targets):
        """Reset the InteractiveShell."""
    
    def resetAll():
        """"""
    
    def status(targets):
        """Return the status of engines"""
    
    def statusAll():
        """"""
    
    def kill(targets):
        """Kills the engine process"""
    
    def killAll():
        """"""
    

# the controller interface implements both IEngineCompleteController, IMultiEngine
class IController(IRemoteController, IMultiEngine):
    
    pass 

# implementation of the Controller Service
def addAllMethods(obj, interface=IMultiEngine):
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



class ControllerService(service.Service):
    """This service listens for kernel engines and control clients.
        It manages the command queues for the engines.
    """
    
    implements(IController)
    
    def __init__(self, maxEngines=255, saveIDs=False):
        self.saveIDs = saveIDs
        self._notifiers = {}
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
    
    
    #IRemoteController
    
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
        if isinstance(targets, int):
            return [self.engines[targets]]
        elif isinstance(targets, (list, tuple)):
            return map(self.engines.get, targets)
        elif targets == 'all':
            return self.engines.values()
        else:
            return []
    
    #IMultiEngine methods
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
        """Execute lines of Python code."""
        
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
        """Push value into locals namespace with name key."""
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
    
    def status(self, targets):
        log.msg("retrieving status of %s" %targets)
        engines = self.engineList(targets)
        l = []
        for e in engines:
            l.append(e.status().addCallback(lambda s:(e.id, s)))
        return gatherBoth(l)
    
    
    # notification methods    
        
    def notifiers(self):
        return self._notifiers
    
    def addNotifier(self, n):
        if n not in self._notifiers:
            self._notifiers[n] = results.INotifier(n)
            self._notifiers[n].notifyOnDisconnect(self.delNotifier,n)
            log.msg("Notifiers: %s" % self._notifiers)
        return defer.succeed(None)
    
    def delNotifier(self, n):
        if n in self._notifiers:
            try:
                del self._notifiers[n]
            except KeyError:
                pass
            log.msg("Notifiers: %s" % self._notifiers)
        return defer.succeed(None)
    
    def notify(self, result):
        for tonotify in self.notifiers().values():
            tonotify.notify(result)
        return result
    

