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

from ipython1.kernel.remoteengine import RemoteEngine

# Interface for the Controller Service

class IControllerService(Interface):
    """The Interface for the IP Controller Service"""
    
    def restartEngine(self, id):
        """Stops and restarts an engine process."""
    
    def cleanQueue(self, id):
        """Cleans out pending commands in an engine's queue."""
    
    def registerEngine(self, connection):
        """register new engine connection"""
    
    def unregisterEngine(self, id):
        """eliminate remote engine object"""
    
    def reconnectEngine(self, id):
        """handle reconnecting engine"""
    
    def disconnectEngine(self, id):
        """handle disconnecting engine"""
    
    def interruptEngine(self, id):
        """send interrupt signal to engine"""
    
#implementation of the Controller Service
        
class ControllerService(service.Service):
    """This service listens for kernel engines and control clients.
    
    """
    
    implements(IControllerService)
    
    def __init__(self, cPort=None, cFactory=None, rEPort=None, rEFactory=None,
                    saveIDs=False):
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
        id = self.availableID.pop()
        self.engine[id] = RemoteEngine(self, id, connection)
        log.msg("registered engine %r" %id)
        return id
    
    def unregisterEngine(self, id):
        log.msg("unregistered engine %r" %id)
        _ = self.engine.pop(id)
        self.availableID.append(id)#need to be able to choose this
    
    def reconnectEngine(self, id, connection):
        #if we want to keep the engine, reconnect to it, for now get a new one|
        try:
            if self.engine[id] is 'restarting':
                log.msg("reconnected engine %r" %id)
                self.engine[id] = RemoteEngine(self, id, connection)
                d = connection.callRemote('getRestart'
                    ).addCallback(self.engine[id].setRestart)
                return d
            else:
                raise Exception('illegal reconnect')
        except KeyError:
            raise Exception('illegal reconnect id')
        except:
            raise
    
    def disconnectEngine(self, id):
        #do I want to keep the RemoteEngine object or not?
        #for now, no
        log.msg("engine %r disconnected" %id)
        if not self.saveIDs:
            self.unregisterEngine(id)
        elif self.engine[id].restart:
            log.msg("expecting reconnect")
            self.engine[id] = 'restarting'
    
    def submitCommand(self, cmd, id=None):
        if id is not None:
            log.msg("submitting command: %r to #%i" %(cmd, id))
            return self.engine[id].submitCommand(cmd)
        else:
            log.msg("submitting command: %r to all" %cmd)
            l = []
            for e in self.engine.values():
                if e not in [None, 'restarting']:
                    d = e.submitCommand(cmd)
                    l.append(d)
            return defer.DeferredList(l)
                
        
    def restartEngine(self, id=None):
        if id is not None:
            log.msg("restarting engine %r" %id)
            d = self.engine[id].setRestart(True)
            d.addCallback(lambda _:self.engine[id].restartEngine())
            return d
    
    def cleanQueue(self, id=None):
        """Cleans out pending commands in the kernel's queue."""
        log.msg("cleaned queue %r" %id)
        self.engine[id].queued = []
    
    def interruptEngine(self, id=None):
        """Send SIGUSR1 to the kernel engine to stop the current command."""
        log.msg("interrupted engine %r" %id)
        if self.engine[id].currentCommand:
            pass
            #do we still want this?
    
    
    # extra methods for testing, inherited from kernel2p.kernelservice
        
    def testCommands(self, id):

        d = self.engine[id].execute("import time")
        d.addCallback(self.printer)
        d = self.engine[id].execute("time.sleep(10)")
        d.addCallback(self.printer)        
        d = self.engine[id].execute("a = 5")
        d.addCallback(self.printer)
        d = self.engine[id].execute("b = 10")
        d.addCallback(self.printer)
        d = self.engine[id].execute("c = a + b")
        d.addCallback(self.printer)
        d = self.engine[id].execute("print c")
        d.addCallback(self.printer)
        
    def printer(self, stuff):
        log.msg("Completed: " + repr(stuff))