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
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import cPickle as pickle

from twisted.application import service, internet
from twisted.internet import protocol, reactor, defer
from twisted.protocols import basic
from twisted.python import log
from twisted.spread import pb
from zope.interface import Interface, implements

from ipython1.kernel.engineservice import Command, IEngineComplete
from ipython1.kernel.serialized import Serialized

#from the Python Cookbook:
def curry(f, *args, **kwargs):
    def curried(*more_args, **more_kwargs):
        dikt = dict(more_kwargs)
        dikt.update(kwargs)
        return f(*(args+more_args), **dikt)
    
    return curried

def setAllMethods(obj, methods=[]):
    if not methods:
        methods = ['execute', 'push','pushSerialized', 'pull','pullSerialized',
            'pullNamespace', 'pullNamespaceSerialized','getResult', 'status', 
            'reset', 'kill', 'clearQueue']
    for m in methods:
        try:
            setattr(obj, m+'All', curry(getattr(obj, m), 'all'))
        except AttributeError:
            #will only add All method if original method exists
            pass


class ResultReporterProtocol(protocol.DatagramProtocol):
    
    def __init__(self, result, addr):
        self.result = result
        self.addr = addr
    
    def startProtocol(self):
        package = pickle.dumps(self.result, 2)
        self.transport.write("RESULT %i %s" % (len(package), package), 
            self.addr)
        self.tried = True
    
    def datagramReceived(self,data, sending_addr):
        if sending_addr == self.addr and data == "RESULT OK":
            self.transport.stopListening()
    


# Interface for the Controller Service

class IRemoteController(Interface):
    """The Interface the controller exposes to remote engines"""
    
    def registerEngine(remoteEngine):
        """register new remote engine"""
    
    def disconnectEngine(id):
        """handle disconnecting engine"""
    
    def registerSerializationTypes(self, *serialTypes):
        """Register the set of allowed subclasses of Serialized."""
        
class IMultiEngine(Interface):
    """interface to multiple objects implementing IEngineComplete"""
    
    def verifyTargets(targets):
        """verify if targets is callable id list, id, or string 'all'"""
    
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
    
    def pullNamespaceSerialized(targets, *keys):
        """Gets a serialized namespace dict from targets by keys."""
    
    def pullNamespaceSerializedAll(*keys):
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
    

#the controller interface implements both IEngineCompleteController, IMultiEngine
class IController(IRemoteController, IMultiEngine):
    
    pass 

#implementation of the Controller Service
        
class ControllerService(service.Service):
    """This service listens for kernel engines and control clients.
        It manages the command queues for the engines.
    """
    
    implements(IController)
    
    def __init__(self, maxEngines=255, saveIDs=False):
        self.saveIDs = saveIDs
        self.notifierFactory = NotifierFactory(self)
        self._notifiers = {}
        self.engines = {}
        self.availableIDs = range(maxEngines,-1,-1)#[255,...,0]
        self.serialTypes = ()
        self.setAutoMethods()
        setAllMethods(self)
    
    def setAutoMethods(self):
        for m in IMultiEngine:
            if callable(IMultiEngine[m]) and m[-3:] != 'All'\
                and getattr(self, m, None) is None:
                print m
                setattr(self, m, curry(self.autoMethod, m))
    
    #a method template for dynamically building methods
    def autoMethod(self, name, targets, *args, **kwargs):
        log.msg("%s on %s" %(name, targets))
        engines = self.engineList(targets)
        l = []
        if not isinstance(targets, int) and len(targets) > 1:
            for e in engines:
                l.append(getattr(e, name)(*args, **kwargs))
            d = defer.gatherResults(l)
        else:
            d = getattr(engines[0], name)(*args, **kwargs)
        return d
    
    #IRemoteController
    
    def registerEngine(self, remoteEngine, id):
        """register new engine connection"""
        for base in IEngineComplete.getBases():
            assert(base.providedBy(remoteEngine))
        
        if id in self.engines.keys():
            raise IdInUse
            
        if id in self.availableIDs:
            remoteEngine.id = id
            self.availableIDs.remove(id)
        else:
            id = self.availableIDs.pop()
            remoteEngine.id = id
            
        remoteEngine.service = self
        self.engines[id] = remoteEngine
        log.msg("registered engine %i" %id)
        return id
    
    def unregisterEngine(self, id):
        """eliminate remote engine object"""
        log.msg("unregistered engine %i" %id)
        del self.engines[id]
        if not self.saveIDs:
            self.availableIDs.append(id)
        else:
            log.msg("preserving id %i" %id)
    
    def disconnectEngine(self, id):
        """handle disconnecting engine"""
        #do I want to keep the RemoteEngine object or not?
        #for now, no
        log.msg("engine %i disconnected" %id)
        self.unregisterEngine(id)
    
    def registerSerializationTypes(self, *serialTypes):
        """Register the set of allowed subclasses of Serialized."""
        self.serialTypes = serialTypes
    
    #ImultiEngine helper methods
    def engineList(self, targets):
        """parse a *valid* id list into list of engines"""
        if isinstance(targets, int):
            return [self.engines[targets]]
        elif isinstance(targets, list):
            return map(self.engines.__getitem__, targets)            
        elif targets is 'all':
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
                else: 
                    return True
        elif targets is 'all':
            return True
        else:
            return False
    
    def pushSerialized(self, targets, **namespace):
        """Push value into locals namespace with name key."""
        log.msg("pushing to %s" % targets)
        engines = self.engineList(targets)
        l = []
        # Call unpack on values that aren't registered as allowed Serialized types
        for k, v in namespace.iteritems():
            if not isinstance(v, self.serialTypes) and isinstance(v, Serialized):
                    log.msg("unpacking serial, ", k)
                    namespace[k] = v.unpack()
        for e in engines:
            l.append(e.pushSerialized(**namespace))
        return defer.gatherResults(l)
    
    def pull(self, targets, *keys):
        """Gets an item out of the self.locals dict by key."""
        log.msg("getting %s from %s" %(keys, targets))
        engines = self.engineList(targets)
        if not isinstance(targets, int) and len(targets) > 1:
            l = []
            for e in engines:
                l.append(e.pull(*keys))
            d = defer.gatherResults(l)
            if len(keys) > 1:
                d.addCallback(lambda resultList: zip(*resultList))
        else:
            d = engines[0].pull(*keys)
        return d
    
    def pullSerialized(self, targets, *keys):
        """Gets an item out of the self.locals dict by key."""
        log.msg("getting %s from %s" %(keys, targets))
        engines = self.engineList(targets)
        if not isinstance(targets, int) and len(targets) > 1:
            l = []
            for e in engines:
                l.append(e.pullSerialized(*keys))
            d = defer.gatherResults(l)
            if len(keys) > 1:
                d.addCallback(lambda resultList: zip(*resultList))
        else:
            d = engines[0].pullSerialized(*keys)
        return d
    
    def status(self, targets):
        log.msg("retrieving status of %s" %targets)
        engines = self.engineList(targets)
        if not isinstance(targets, int) and len(targets) > 1:
            l = []
            dikt = {}
            for e in engines:
                l.append(e.status().addCallback(lambda s: 
                                dikt.__setitem__(e.id, s)))
            d = defer.gatherResults(l).addCallback(lambda _: dikt)
        else:
            d = engines[0].status()
        return d
    
    
    #notification methods    
        
    def notifiers(self):
        return self._notifiers
    
    def addNotifier(self, n):
        if n not in self._notifiers:
            self._notifiers[n] = reactor.connectTCP(n[0], n[1], self.notifierFactory)
            self.notifierFactory.lastNotifier = n
            log.msg("Notifiers: %s" % self._notifiers)
        return defer.succeed(None)
    
    def delNotifier(self, n):
        if n in self._notifiers:
            self._notifiers[n].disconnect()
            try:
                del self._notifiers[n]
            except KeyError:
                pass
            log.msg("Notifiers: %s" % self._notifiers)
        return defer.succeed(None)
    
    def notify(self, id, result):
        package = pickle.dumps((id, result), 2)
        for tonotify in self.notifiers().values():
            if tonotify.transport.protocol is not None:
                tonotify.transport.protocol.sendLine(
                        "RESULT %i %s" %(len(package), package))
            else:
                log.msg("Notifier connection not ready for RESULT " + str((id, result)))
        return result
    

class NotifierFactory(protocol.ClientFactory):
    """A small client factory and protocol for the tcp results gatherer"""
    protocol = basic.LineReceiver
    protocol.lineReceived = lambda _,__: None
    lastNotifier = None
    def __init__(self, service):
        self.service = service
    
    def clientConnectionLost(self, connector, reason):
        self.service.delNotifier((connector.host, connector.port))
    
    clientConnectionFailed = clientConnectionLost
    
