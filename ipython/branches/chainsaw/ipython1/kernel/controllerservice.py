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
    """Adds a few control methods to the IPythonCoreService API"""
    
    def restartEngine(self, id):
        """Stops and restarts an engine process."""
    
    def cleanQueue(self, id):
        """Cleans out pending commands in an engine's queue."""
    
    def registerEngine(self, connection):
        """register new engine connection"""
    
    def unregisterEngine(self, id):
        """"""
    
    def reconnectEngine(self, id):
        """"""
    
    def disconnectEngine(self, id):
        """"""
    
    def interruptEngine(self, id):
        """"""
    
#implementation of the Controller Service
        
class ControllerService(service.Service):
    """This service listens for kernel engines and control clients.
    
    """
    
    implements(IControllerService)
    
    def __init__(self, cPort=None, cFactory=None, rEPort=None, rEFactory=None):
        """controlFactory listens for users, 
        remoteEngineFactory listens for engines"""
        if None not in [cPort, cFactory]:
            self.setupControlFactory(cPort, cFactory)
        if None not in [rEPort, rEFactory]:
            self.setupRemoteEngineFactory(rEPort, rEFactory)
        self.engine = {}
        self.availableID = range(128,-1,-1)#[128,...,0]
    
    def setupControlFactory(self, cPort, cFactory):
        self.controlPort = cPort
        self.controlFactory = cFactory
        self.controlFactory.service = self
    
    def setupRemoteEngineFactory(self, rEPort, rEFactory):
        self.remoteEnginePort = rEPort
        self.remoteEngineFactory = rEFactory
        self.remoteEngineFactory.service = self
        
    def startService(self):
        self.controlServer = reactor.listenTCP(self.controlPort, self.controlFactory)
        self.engineServer = reactor.listenTCP(self.remoteEnginePort, self.remoteEngineFactory)
        service.Service.startService(self)
    
    def stopService(self):
        self.controlServer.stopListening()
        self.engineServer.stopListening()
        d = service.Service.stopService(self)
        return d
    
    def registerEngine(self, connection):
        id = self.availableID.pop()
        self.engine[id] = RemoteEngine(self, id, connection)
        log.msg("registered engine %r" %id)
        return id
    
    def unregisterEngine(self, id):
        _ = self.engine.pop(id)
        self.availableID.append(id)#need to be able to choose this
        log.msg("unregistered engine %r" %id)
    
    def reconnectEngine(self, id, connection):
        #if we want to keep the engine, reconnect to it, for now get a new one|
        if self.engine[id] is 'restarting':
            self.engine[id] = RemoteEngine(connection)
        else:
            raise 'illegal reconnect'
        log.msg("reconnected engine %r" %id)
    
    def disconnectEngine(self, id):
        #do I want to keep the RemoteEngine object or not?
        #for now, no
        log.msg("engine %r disconnected" %id)
        if not self.engine[id].holdID:
            self.unregisterEngine(id)
        elif self.engine[id].restart:
            self.engine[id] = 'restarting'
            log.msg("expecting reconnect")

    def restartEngine(self, id):
        """Stops and restarts the kernel engine process."""
        #send restart command
        log.msg("restarting engine %r" %id)
    
    def cleanQueue(self, id):
        """Cleans out pending commands in the kernel's queue."""
        self.engine[id].queued = []
        log.msg("cleaned queue %r" %id)
    
    def interruptEngine(self, id):
        """Send SIGUSR1 to the kernel engine to stop the current command."""
        if self.engine[id].currentCommand:
            pass
            #do we still want this?
        log.msg("interrupted engine %r" %id)
    
    
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