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


from twisted.application import service
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
    """This service listens for kernel engines and talks to them over PB.
    
    There are two steps in starting the kernel engine.  First, spawnProcess
    is called to start the actual process.  Then it can be connected to over
    PB.  If the process dies, it will automatically be restarted and re-
    connected to.  But if the connection fails, but the process doesn't, there
    will be a fatal error.  This needs to be fixed by having the PB Factory
    automatically reconnect.
    """
    
    implements(IControllerService)
    
    def __init__(self, cPort, cFactory, rEPort, rEFactory):
        """controlFactory listens for users, 
        remoteEngineFactory listens for engines"""
        self.controlPort = cPort
        self.controlFactory = cFactory
        self.controlFactory.service = self
        self.remoteEnginePort = rEPort
        self.remoteEngineFactory = rEFactory
        self.remoteEngineFactory.service = self
        self.engine = {}
        self.availableId = range(128,0,-1)
    
    def startService(self):
        service.Service.startService(self)
        reactor.listenTCP(self.controlPort, self.controlFactory)
        reactor.listenTCP(self.remoteEnginePort, self.remoteEngineFactory)
    
    def registerEngine(self, connection):
        id = self.availableId.pop()
        self.engine[id] = RemoteEngine(id, connection)
        log.msg("registered engine %r" %id)
        return id
    
    def unregisterEngine(self, id):
        (key, engine) = self.engine.pop(id)
        del engine
        self.availableId.append(key)#need to be able to choose this
        log.msg("unregistered engine %r" %id)
    
    def reconnectEngine(self, id, connection):
        #if we want to keep the engine, reconnect to it - for now,a new one
        self.engine[id] = RemoteEngine(connection)
        log.msg("reconnected engine %r" %id)
    
    def disconnectEngine(self, id):
        #do I want to keep the RemoteEngine or not?
        #for now, no
        self.engine[id] = None
        log.msg("disconnected engine %r" %id)

    def restartEngine(self, id):
        """Stops and restarts the kernel engine process."""
        #send restart command
        self.disconnectEngine(id)
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