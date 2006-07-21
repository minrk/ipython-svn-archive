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


from twisted.application import service, internet
from twisted.internet import protocol, reactor, defer
from twisted.python import log
from zope.interface import Interface, implements
from twisted.spread import pb

from ipython1.kernel.remoteengine import RemoteEngine, Command

# Interface for the Controller Service

class IControllerService(Interface):
    """The Interface for the IP Controller Service"""
    
    def registerEngine(self, connection):
        """register new engine connection"""
    
    def unregisterEngine(self, id):
        """eliminate remote engine object"""
    
    def reconnectEngine(self, id):
        """handle reconnecting engine"""
    
    def disconnectEngine(self, id):
        """handle disconnecting engine"""
    
    def restartEngine(self, id):
        """Stops and restarts an engine process."""
    
    def cleanQueue(self, id):
        """Cleans out pending commands in an engine's queue."""
    
    def interruptEngine(self, id):
        """Send SIGUSR1 to the kernel engine to stop the current command."""
    

#implementation of the Controller Service
        
class ControllerService(service.Service):
    """This service listens for kernel engines and control clients.
        It manages the command queues for the engines.
    """
    
    implements(IControllerService)
    
    def __init__(self, cPort=None, cFactory=None,       #):
                rEPort=None, rEFactory=None,saveIDs=False):
        """controlFactory listens for users, 
        remoteEngineFactory listens for engines"""
        if None not in [cPort, cFactory]:
            self.setupControlFactory(cPort, cFactory)
        if None not in [rEPort, rEFactory]:
            self.setupRemoteEngineFactory(rEPort, rEFactory)
        self.saveIDs = saveIDs
        self.engine = {}
        self.availableID = range(127,-1,-1)#[127,...,0]
    
    
    def setupControlFactory(self, cPort, cFactory):
        self.controlPort = cPort
        self.controlFactory = cFactory
        self.controlFactory.service = self
    
    def setupRemoteEngineFactory(self, rEPort, rEFactory):
        self.remoteEnginePort = rEPort
        self.remoteEngineFactory = rEFactory
        self.remoteEngineFactory.service = self
    
    def startService(self):
        self.controlServer = reactor.listenTCP(self.controlPort,
                        self.controlFactory)
        self.engineServer = reactor.listenTCP(self.remoteEnginePort, 
                        self.remoteEngineFactory)
        service.Service.startService(self)
    
    def stopService(self):
        d0 = self.controlServer.stopListening()
        d1 = self.engineServer.stopListening()
        d2 = service.Service.stopService(self)
        l = []
        for d in [d0, d1, d2]:
            if d is not None:
                l.append(d)
        if l:
            return defer.DeferredList(l)
        else:
             return None
    
    def registerEngine(self, connection):
        """register new engine connection"""
        id = self.availableID.pop()
        self.engine[id] = RemoteEngine(self, id, connection)
        log.msg("registered engine %i" %id)
        return id
    
    def unregisterEngine(self, id):
        """eliminate remote engine object"""
        log.msg("unregistered engine %i" %id)
        e = self.engine.pop(id)
        del e
        if self.saveIDs:
            log.msg("preserving id %i" %id)
            self.availableID.append(id)
    
    def reconnectEngine(self, id, connection):
        """handle reconnecting engine"""
        #if we want to keep the engine, reconnect to it, for now get a new one|
        try:
            if self.engine[id] is 'restarting':
                log.msg("reconnected engine %i" %id)
                self.engine[id] = RemoteEngine(self, id, connection, 
                        restart=True)
            else:
                raise Exception('illegal reconnect')
        except KeyError:
            raise Exception('illegal reconnect id')
        except:
            raise
    
    def disconnectEngine(self, id):
        """handle disconnecting engine"""
        #do I want to keep the RemoteEngine object or not?
        #for now, no
        log.msg("engine %i disconnected" %id)
        if self.engine[id].restart:
            log.msg("expecting reconnect")
            self.engine[id] = 'restarting'
        else:
            self.unregisterEngine(id)
    
    def submitCommand(self, cmd, id='all'):
        log.msg("submitting command: %s to #%s" %(cmd, id))
        if id is not 'all':
            return self.engine[id].submitCommand(cmd)
        else:
            l = []
            for e in self.engine.values():
                if e is not 'restarting':
                    command = Command(cmd.remoteMethod, *cmd.args)
                    d = e.submitCommand(command)
                    l.append(d)
            return defer.DeferredList(l)
    
    tellAll = submitCommand
    def restartEngine(self, id='all'):
        """Stops and restarts an engine service."""
        log.msg("restarting engine: %s" %id)
        self.cleanQueue(id)
        if id is not 'all':
            d = self.engine[id].setRestart(True)
            d.addCallback(lambda _:self.engine[id].restartEngine())
            return d
        else:
            l = []
            for e in self.engine.values():
                if e is not 'restarting':
                    d = e.setRestart(True)
                    d.addCallback(lambda _:e.restartEngine())
                    l.append(d)
            return defer.DeferredList(l)
    
    def cleanQueue(self, id='all'):
        """Cleans out pending commands in the kernel's queue."""
        log.msg("cleaning queue %s" %id)
        if id is not 'all':
            self.engine[id].queued = []
        else:
            for e in self.engine.values():
                if e is not 'restarting':
                    e.queued = []
    
    def interruptEngine(self, id='all'):
        """Send SIGUSR1 to the kernel engine to stop the current command."""
        log.msg("(did not) interrupted engine %s" %id)
        if self.engine[id].currentCommand:
            pass
            #not implemented
    
