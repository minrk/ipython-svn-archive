"""A Twisted Service for the Controller

TODO:

- Use subclasses of pb.Error to pass exceptions back to the calling process.
- Deal more carefully with the failure modes of the kernel engine.  The
  PbFactory should be make to reconnect possibly.
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

from ipython1.kernel.engineservice import Command
from ipython1.kernel.kernelerror import *

#from the Python Cookbook:
def curry(f, *args, **kwargs):
    def curried(*more_args, **more_kwargs):
        dikt = dict(more_kwargs)
        dikt.update(kwargs)
        return f(*(args+more_args), **dikt)
    
    return curried

def setAllMethods(obj):
    methods = ['execute', 'push', 'pull', 'pullNamespace',
            'getResult', 'status', 'reset', 'kill']
    for m in methods:
        setattr(obj, m+'All', curry(getattr(obj, m), 'all'))


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
    
    #not sure if this one should be exposed in the interface
    def disconnectEngine(id):
        """handle disconnecting engine"""
    

class IMultiEngine(Interface):
    """interface to multiple objects implementing IEngine"""
    
    def verifyTargets(targets):
        """verify if ids is callable id list"""
    
    #IQueuedEngine multiplexer methods
    def cleanQueue(targets):
        """Cleans out pending commands in an engine's queue."""
    
    def cleanQueueAll():
        """Cleans out pending commands in an engine's queue."""
    
    #IEngine multiplexer methods
    def execute(targets, lines):
        """Execute lines of Python code."""
    
    def executeAll(lines):
        """Execute lines of Python code."""
    
    def executeAll(targets, lines):
        """"""
    
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
    

#the controller interface implements both IEngineController, IMultiEngine
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
        setAllMethods(self)
    
    #IRemoteController
    
    def registerEngine(self, remoteEngine, id):
        """register new engine connection"""
        if id in self.engines.keys():
            raise IdInUse
            return
            
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
    
    def cleanQueue(self, targets):
        """Cleans out pending commands in the kernel's queue."""
        log.msg("cleaning queue %s" %targets)
        engines = self.engineList(targets)
        if not engines:
            return defer.succeed(None)
        l = []
        for e in engines:
            l.append(e.cleanQueue())
        return defer.gatherResults(l)
    
    def cleanQueueAll(self):
        return self.cleanQueue('all')
    
    def execute(self, targets, lines):
        """Execute lines of Python code."""
        log.msg("executing %s on %s" %(lines, targets))
        engines = self.engineList(targets)
        l = []
        for e in engines:
            d = e.execute(lines)
            self.executeCallback(e.id, d)
            l.append(d)
        return defer.gatherResults(l)
    
    def executeAll(self, lines):
        return self.execute('all', lines)
    
    def executeCallback(self, id, d):
        d.addCallback(lambda r:self.notify(id, r))
    
    def push(self, targets, **namespace):
        """Push value into locals namespace with name key."""
        log.msg("pushing to %s" % targets)
        engines = self.engineList(targets)
        l = []
        for e in engines:
            l.append(e.push(**namespace))
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
    
    def pullNamespace(self, targets, *keys):
        """Gets an item out of the self.locals dict by key."""
        log.msg("getting namespace %s from %s" %(keys, targets))
        engines = self.engineList(targets)
        if not isinstance(targets, int) and len(targets) > 1:
            l = []
            for e in engines:
                l.append(e.pullNamespace(*keys))
            d = defer.gatherResults(l)
            if len(keys) > 1:
                d.addCallback(lambda resultList: zip(*resultList))
        else:
            d = engines[0].pullNamespace(*keys)
        return d
    
    def status(self, targets):
        log.msg("retrieving status of %s" %targets)
        engines = self.engineList(targets)
        l = []
        dikt = {}
        for e in engines:
            l.append(e.status().addCallback(lambda s: 
                            dikt.__setitem__(e.id, s)))
        return defer.gatherResults(l).addCallback(lambda _: dikt)
    
    def reset(self, targets):
        """Reset the InteractiveShell."""
        log.msg("resetting %s" %(targets))
        engines = self.engineList(targets)
        l = []
        for e in engines:
            l.append(e.reset())
        return defer.gatherResults(l)
    
    def kill(self, targets):
        log.msg("killing %s" %(targets))
        engines = self.engineList(targets)
        l = []
        for e in engines:
            l.append(e.kill())
        return defer.gatherResults(l)
    
    def getResult(self, targets, i=None):
        """Get the stdin/stdout/stderr of command i."""
        if i is not None:
            log.msg("getting result %s from %s" %(i, targets))
        else:
            log.msg("getting last result from %s" %targets)
        engines = self.engineList(targets)
        l = []
        for e in engines:
            l.append(e.getResult(i))
        return defer.gatherResults(l)
    
    
    
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
    
