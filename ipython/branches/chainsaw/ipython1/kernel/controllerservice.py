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

import os, signal

from twisted.application import service
from twisted.internet import protocol, reactor, defer
from twisted.python import log
from zope.interface import Interface, implements
from twisted.spread import pb

from ipython1.kernel import engineservice
from ipython1.kernel.remoteengine import RemoteEngine

# Classes for the Controller Service

class IControllerService(engineservice.IEngine):
    """Adds a few control methods to the IPythonCoreService API"""
    
    def restartEngine(self, id):
        """Stops and restarts an engine process."""
        
    def cleanQueue(self, id):
        """Cleans out pending commands in an engine's queue."""
        
    def interruptEngine(self, id):
        """Send SIGINT to the engine."""
    
    def registerEngine(self, protocol):
        """register new engine connection"""
        
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
    
    def __init__(self, controlPort, controlFactory, remoteEnginePort, 
            remoteEngineFactory):
        """controlFactory listens for users, 
        remoteEngineFactory listens for engines"""
        self.controlPort = controlPort
        self.controlFactory = controlFactory
        controlFactory.service = self
        self.remoteEnginePort = remoteEnginePort
        self.remoteEngineFactory = remoteEngineFactory
        remoteEngineFactory.service = self
        self.engine = {}
        self.availableId = range(128,0,-1)
    
    def outReceived(self, id, data):
        """Called when the Kernel Engine process writes to stdout."""
        #log.msg(data)
    
    def errReceived(self, id, data):
        """Called when the Kernel Engine process writes to stdout."""
        log.msg("%r:" %id  +data)   
    
    # Methods to manage the Engines
    
    def startService(self):
        service.Service.startService(self)
        reactor.listenTCP(self.controlPort, self.controlFactory)
        reactor.listenTCP(self.remoteEnginePort, self.remoteEngineFactory)
    
    
    def registerEngine(self, protocol):
        id = self.availableId.pop()
        log.msg("registering engine %r" %id)
        self.engine[id] = RemoteEngine(id, protocol, self.remoteEngineFactory)
    
    def stopRemoteEngineProcess(self, id):
        self.engine[id].autoStart = False   # Don't restart automatically after killing
        self.disconnectRemoteEngineProcess(id)
        #os.kill(self.kernelEngineProcessProtocol.transport.pid, 
        #    signal.SIGKILL)

    def restartRemoteEngineProcess(self, id):
        self.engine[id].autoStart = True
#todo   send restart notify
        self.disconnectRemoteEngineProcess(id)
        #os.kill(self.kernelEngineProcessProtocol.transport.pid, 
        #    signal.SIGKILL)

    def handleRemoteEngineProcessEnding(self, id, status):
        """Called when the kenel engine process ends & decides to restart.
        
        The status object has info about the exit code, but currently I am
        not using it.
        """
        
        if self.engine[id].autoStart:
#todo            self.startKernelEngineProcess()
            log.msg("Kernel Engine Process Restarting")
        else:
            log.msg("Kernel Engine Process Stopped")
        
    # Methods to manage the PB connection to the Remote Engine Process 
        
    def testCommands(self, id):

        d = self.engine[id].execute("import time")
        d.addCallback(self.printer)
        d = self.engine[id].execute("time.sleep(10)")
        d.addCallback(self.printer)        
        reactor.callLater(3,self.interrupt_engine, id)
        
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

    def disconnectKernelEngineProcess(self, id):
        if self.engine[id].factory:
            self.engine[id].PBFactory.disconnect()
        #self.currentCommand = None
        self.rootObject = None
        self.kernelEnginePBFactory = None

    # Interface methods unique to the IControllerService interface
    
    def restartEngine(self, id):
        """Stops and restarts the kernel engine process."""
        self.cleanQueue(id)
        self.restartKernelEngineProcess(id)
        
    def cleanQueue(self, id):
        """Cleans out pending commands in the kernel's queue."""
        self.engine[id].queued = []

    def interruptEngine(self, id):
        """Send SIGUSR1 to the kernel engine to stop the current command."""
        if self.engine[id].currentCommand:
            pass
            #os.kill(self.kernelEngineProcessProtocol.transport.pid, signal.SIGUSR1)
