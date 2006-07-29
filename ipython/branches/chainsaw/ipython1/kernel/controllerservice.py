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
from zope.interface import Interface, implements
from twisted.spread import pb

from ipython1.kernel.engineservice import Command
from ipython1.kernel.kernelerror import *

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
    
    def registerEngine(self, remoteEngine):
        """register new remote engine"""
    
    #not sure if this one should be exposed in the interface
    def disconnectEngine(self, id):
        """handle disconnecting engine"""
    

class IMultiEngine(Interface):
    """interface to multiple objects implementing IEngine"""
    
    def verifyIds(self, ids):
        """verify if ids is callable id list"""
    
    def engineList(self, ids):
        """parse a *valid* id list into list of engines"""
    
    #IQueuedEngine multiplexer methods
    def cleanQueue(self, ids='all'):
        """Cleans out pending commands in an engine's queue."""
    
    #IEngine multiplexer methods
    def execute(self, lines, ids='all'):
        """Execute lines of Python code."""
    
    def put(self, key, value, ids='all'):
        """Put value into locals namespace with name key."""
    
    def putPickle(self, key, package, ids='all'):
        """Unpickle package and put into the locals namespace with name key."""
    
    def get(self, key, ids='all'):
        """Gets an item out of the self.locals dict by key."""
    
    def getPickle(self, key, ids='all'):
        """Gets an item out of the self.locals dist by key and pickles it."""
    
    def update(self, dictOfData, ids='all'):
        """Updates the self.locals dict with the dictOfData."""
    
    def updatePickle(self, dictPickle, ids='all'):
        """Updates the self.locals dict with the pickled dict."""
    
    def reset(self, ids='all'):
        """Reset the InteractiveShell."""
    
    def status(self, ids='all'):
        """Return the status of engines"""

    def getCommand(self, i=None, ids='all'):
        """Get the stdin/stdout/stderr of command i."""
    
    def getLastCommandIndex(self, ids='all'):
        """Get the index of the last command."""
    

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
        self.availableIDS = range(maxEngines,-1,-1)#[255,...,0]
    
    #IRemoteController
    
    def registerEngine(self, remoteEngine, id):
        """register new engine connection"""
        if id in self.engines.keys():
            raise IdInUse
            return
            
        if id in self.availableIDS:
            remoteEngine.id = id
            self.availableIDS.remove(id)
        else:
            id = self.availableIDS.pop()
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
            self.availableIDS.append(id)
        else:
            log.msg("preserving id %i" %id)
    
    def disconnectEngine(self, id):
        """handle disconnecting engine"""
        #do I want to keep the RemoteEngine object or not?
        #for now, no
        log.msg("engine %i disconnected" %id)
        self.unregisterEngine(id)
    
    
    #IMultiEngine methods
    def verifyIds(self, ids):
        if isinstance(ids, int):
            if ids not in self.engines.keys():
                log.msg("id %i not registered" %ids)
                return False
            else: 
                return True
        elif isinstance(ids, list):
            for id in ids:
                if id not in self.engines.keys():
                    log.msg("id %i not registered" %id)
                    return False
                else: 
                    return True
        elif ids is 'all':
            return True
        else:
            return False
    
            
    def engineList(self, ids):
        """parse a *valid* id list into list of engines"""
        if isinstance(ids, int):
            return [self.engines[ids]]
        elif isinstance(ids, list):
            return map(self.engines.__getitem__, ids)            
        elif ids is 'all':
            return self.engines.values()
        else:
            return []
    
    def cleanQueue(self, ids='all'):
        """Cleans out pending commands in the kernel's queue."""
        log.msg("cleaning queue %s" %ids)
        engines = self.engineList(ids)
        if not engines:
            return defer.succeed(None)
        l = []
        for e in engines:
            l.append(e.cleanQueue())
        return defer.gatherResults(l)
    
    def execute(self, lines, ids='all'):
        """Execute lines of Python code."""
        log.msg("executing %s on %s" %(lines, ids))
        engines = self.engineList(ids)
        l = []
        id = 1
        for e in engines:
            id = id+4
            l.append(e.execute(lines).addCallback(self.notify))
        return defer.gatherResults(l)
    
    def put(self, key, value, ids='all'):
        """Put value into locals namespace with name key."""
        log.msg("putting %s=%s on %s" %(key, value, ids))
        engines = self.engineList(ids)
        l = []
        for e in engines:
            l.append(e.put(key, value))
        return defer.gatherResults(l)
    
    def putPickle(self, key, package, ids='all'):
        """Unpickle package and put into the locals namespace with name key."""
        log.msg("putting pickle %s=%s on %s" %(key, pickle.loads(package), ids))
        engines = self.engineList(ids)
        l = []
        for e in engines:
            l.append(e.putPickle(key, package))
        return defer.gatherResults(l)
    
    def get(self, key, ids='all'):
        """Gets an item out of the self.locals dict by key."""
        log.msg("getting %s from %s" %(key, ids))
        engines = self.engineList(ids)
        l = []
        for e in engines:
            l.append(e.get(key))
        return defer.gatherResults(l)
    
    def getPickle(self, key, ids='all'):
        """Gets an item out of the self.locals dist by key and pickles it."""
        log.msg("getting pickle %s from %s" %(key, ids))
        engines = self.engineList(ids)
        l = []
        for e in engines:
            l.append(e.getPickle(key))
        return defer.gatherResults(l)
    
    def update(self, dictOfData, ids='all'):
        """Updates the self.locals dict with the dictOfData."""
        log.msg("updating %s with %s" %(ids, dict))
        engines = self.engineList(ids)
        l = []
        for e in engines:
            l.append(e.update(dictOfData))
        return defer.gatherResults(l)
    
    def updatePickle(self, dictPickle, ids='all'):
        """Updates the self.locals dict with the pickled dict."""
        log.msg("updating %s with pickle %s" %(ids, pickle.loads(dictPickle)))
        engines = self.engineList(ids)
        l = []
        for e in engines:
            l.append(e.updatePickle(dictPickle))
        return defer.gatherResults(l)
    
    def status(self, ids='all'):
        log.msg("retrieving status of %s" %ids)
        engines = self.engineList(ids)
        d = {}
        for e in engines:
            d[e.getID()] = e.status()
        return d
    
    def reset(self, ids='all'):
        """Reset the InteractiveShell."""
        log.msg("resetting %s" %(ids))
        engines = self.engineList(ids)
        l = []
        for e in engines:
            l.append(e.reset())
        return defer.gatherResults(l)
    
    def kill(self, ids='all'):
        log.msg("killing %s" %(ids))
        engines = self.engineList(ids)
        l = []
        for e in engines:
            l.append(e.kill())
        return defer.gatherResults(l)
    
    def getCommand(self, i=None, ids='all'):
        """Get the stdin/stdout/stderr of command i."""
        log.msg("getting command %s from %s" %(i, ids))
        engines = self.engineList(ids)
        l = []
        for e in engines:
            l.append(e.getCommand(i))
        return defer.gatherResults(l)
    
    def getLastCommandIndex(self, ids='all'):
        """Get the index of the last command."""
        log.msg("getting last command index from %s" %(ids))
        engines = self.engineList(ids)
        l = []
        for e in engines:
            l.append(e.getLastCommandIndex())
        return defer.gatherResults(l)
        
    
    
    #notification methods
    
        
    def notifiers(self):
        return self._notifiers
    
    def addNotifier(self, n):
        if n not in self._notifiers:
            self._notifiers[n] = reactor.connectTCP(n[0], n[1], self.notifierFactory)
            self.notifierFactory.lastNotifier = n
            log.msg("Notifiers: %s" % self._notifiers)
        return defer.succeed("OK")
    
    def delNotifier(self, n):
        if n in self._notifiers:
            self._notifiers[n].disconnect()
            del self._notifiers[n]
            log.msg("Notifiers: %s" % self._notifiers)
        return defer.succeed("OK")
    
    def notify(self, result):
        package = pickle.dumps(result, 2)
        for tonotify in self.notifiers().values():
            if tonotify.transport.protocol is not None:
                tonotify.transport.protocol.sendLine(
                        "RESULT %i %s" %(len(package), package))
            else:
                log.msg("Notifier connection not ready for RESULT " + str(result))
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
    
