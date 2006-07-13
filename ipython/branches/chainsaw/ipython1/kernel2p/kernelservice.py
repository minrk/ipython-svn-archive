"""A Twisted Service Representation of the IPython Core

TODO:

- Use subclasses of pb.Error to pass exceptions back to the calling process.
- Deal more carefully with the failure modes of the kernel engine.  The
  PbFactory should be make to reconnect possibly.
- Add an XML-RPC interface
- Add an HTTP interface
- Security!!!!!
"""

import os, signal

from twisted.application import service
from twisted.internet import protocol, reactor, defer
from twisted.python import log
from zope.interface import Interface, implements
from twisted.spread import pb

from ipython1.kernel2p import coreservice

# Classes for the Kernel Service

class Command(object):
    """A command that will be sent to the Kernel Engine."""

    def __init__(self, remoteMethod, *args):
        """Build a new Command object."""
        
        self.remoteMethod = remoteMethod
        self.args = args
        
    def setDeferred(self, d):
        """Sets the deferred attribute of the Command."""
        
        self.deferred = d

    def __repr__(self):
        return "Command: " + self.remoteMethod + repr(self.args)
        
    def handleResult(self, result):
        """When the result is ready, relay it to self.deferred."""
        
        self.deferred.callback(result)
        
    def handleError(self, reason):
        """When an error has occured, relay it to self.deferred."""
        log.msg("Traceback from remote host: " + reason.getErrorMessage())
        self.deferred.errback(reason)

class KernelEngineProcessProtocol(protocol.ProcessProtocol):

    def __init__(self, service):
        self.service = service
        
    def connectionMade(self):
        """Called when the Ke process is running.
        
        This should immediately trigger a connection to the kenel engine process
        over a socket.
        """
        
        # We need to make sure that the kernel engine has really started
        # before connecting to it
        reactor.callLater(2,self.service.connectKernelEngineProcess)
    
    def outReceived(self, data):
        """Let the service decide what to do."""
        
        self.service.outReceived(data)
                
    def errReceivved(self, data):
        """Let the service decide what to do."""
        
        self.service.errReceived(data)
        
    def processEnded(self, status):
        """Let the service decide what to do."""

        self.service.handleKernelEngineProcessEnding(status)
           
class IKernelService(coreservice.ICoreService):
    """Adds a few controll methods to the IPythonCoreService API"""
    
    def restart_engine(self):
        """Stops and restarts the kernel engine process."""
        
    def clean_queue(self):
        """Cleans out pending commands in the kernel's queue."""
        
    def interrupt_engine(self):
        """Send SIGINT to the kernel engine."""
        
class KernelService(service.Service):
    """This service starts the kernel engine and talks to it over PB.
    
    There are two steps in starting the kernel engine.  First, spawnProcess
    is called to start the actual process.  Then it can be connected to over
    PB.  If the process dies, it will automatically be restarted and re-
    connected to.  But if the connection fails, but the process doesn't, there
    will be a fatal error.  This needs to be fixed by having the PB Factory
    automatically reconnect.
    """

    implements(IKernelService)
    
    def __init__(self, port):
        
        self.port = port
        self.autoStart = True
        self.kernelEngineProcessProtocol = None
        self.rootObject = None
        self.kernelEnginePBFactory = None
        self.queued = []
        self.currentCommand = None
        
    def outReceived(self, data):
        """Called when the Kernel Engine process writes to stdout."""
        #log.msg(data)
     
    def errReceived(self, data):
        """Called when the Kernel Engine process writes to stdout."""
        log.msg(data)   

    # Methods to manage the Kernel Engine Process 

    def startService(self):
        service.Service.startService(self)
        # I seem to need this to ensure the reactor is running before
        # spawnProcess is called
        reactor.callLater(2,self.startKernelEngineProcess)
        #reactor.callLater(10,self.restartKernelEngineProcess)
        
    def startKernelEngineProcess(self):
        self.kernelEngineProcessProtocol = KernelEngineProcessProtocol(self)
        reactor.spawnProcess(self.kernelEngineProcessProtocol,
            'ipengine',
            args=['ipengine','-p %i' % self.port],
            env = os.environ)
        self.autoStart = True  # autoStart by default
        
    def stopKernelEngineProcess(self):
        self.autoStart = False   # Don't restart automatically after killing
        self.disconnectKernelEngineProcess()
        os.kill(self.kernelEngineProcessProtocol.transport.pid, 
            signal.SIGKILL)

    def restartKernelEngineProcess(self):
        self.autoStart = True
        self.disconnectKernelEngineProcess()
        os.kill(self.kernelEngineProcessProtocol.transport.pid, 
            signal.SIGKILL)

    def handleKernelEngineProcessEnding(self, status):
        """Called when the kenel engine process ends & decides to restart.
        
        The status object has info about the exit code, but currently I am
        not using it.
        """
        
        if self.autoStart:
            self.startKernelEngineProcess()
            log.msg("Kernel Engine Process Restarting")
        else:
            log.msg("Kernel Engine Process Stopped")
        
    # Methods to manage the PB connection to the Kernel Engine Process 
        
    def connectKernelEngineProcess(self):
        self.kernelEnginePBFactory = pb.PBClientFactory()
        reactor.connectTCP("127.0.0.1", self.port, self.kernelEnginePBFactory)
        self.kernelEnginePBFactory.getRootObject().addCallbacks(self.gotRoot,
                                                    self.gotNoRoot)
                                                                                   
    def gotRoot(self, obj):
        self.rootObject = obj
        self._flushQueue()
        log.msg("Connected to the Kernel Engine.")
        #self.testCommands()
        
    def testCommands(self):

        d = self.execute("import time")
        d.addCallback(self.printer)
        d = self.execute("time.sleep(10)")
        d.addCallback(self.printer)        
        reactor.callLater(3,self.interrupt_engine)
        
        d = self.execute("a = 5")
        d.addCallback(self.printer)
        d = self.execute("b = 10")
        d.addCallback(self.printer)
        d = self.execute("c = a + b")
        d.addCallback(self.printer)
        d = self.execute("print c")
        d.addCallback(self.printer)
        
    def printer(self, stuff):
        log.msg("Completed: " + repr(stuff))
        
    def gotNoRoot(self, reason):
        reason.printDetailedTraceback()

    def disconnectKernelEngineProcess(self):
        if self.kernelEnginePBFactory:
            self.kernelEnginePBFactory.disconnect()
        #self.currentCommand = None
        self.rootObject = None
        self.kernelEnginePBFactory = None

    # The logic of the service

    def submitCommand(self, cmd):
        
        d = defer.Deferred()
        cmd.setDeferred(d)
        if self.currentCommand is not None:
            log.msg("Queueing: " + repr(cmd))
            self.queued.append(cmd)
            return d
        self.currentCommand = cmd
        self.runCurrentCommand()
        return d
    
    def runCurrentCommand(self):
        cmd = self.currentCommand
        log.msg("Starting: " + repr(self.currentCommand))
        d = self.rootObject.callRemote(cmd.remoteMethod, *(cmd.args))
        d.addCallback(self.finishCommand)
        d.addErrback(self.abortCommand)

    def _flushQueue(self):
 
        if len(self.queued) > 0:
            self.currentCommand = self.queued.pop(0)
            self.runCurrentCommand()

    def finishCommand(self, result):
        log.msg("Finishing: " + repr(self.currentCommand) + repr(result))
        self.currentCommand.handleResult(result)
        del self.currentCommand
        self.currentCommand = None
        self._flushQueue()
        return result
        
    def abortCommand(self, reason):
        self.currentCommand.handleError(reason)
        del self.currentCommand
        self.currentCommand = None
        self._flushQueue()
        #return reason

    # Interface methods unique to the IKernelService interface
    
    def restart_engine(self):
        """Stops and restarts the kernel engine process."""
        self.clean_queue()
        self.restartKernelEngineProcess()
        
    def clean_queue(self):
        """Cleans out pending commands in the kernel's queue."""
        self.queued = []

    def interrupt_engine(self):
        """Send SIGUSR1 to the kernel engine to stop the current command."""
        if self.currentCommand:
            os.kill(self.kernelEngineProcessProtocol.transport.pid, signal.SIGUSR1)

    # Methods that should use the queue

    def execute(self, lines):
        """Execute lines of Python code."""
        
        d = self.submitCommand(Command("execute", lines))
        return d

    def put(self, key, value):
        """Put value into locals namespace with name key."""

        d = self.submitCommand(Command("put", key, value))
        return d

    def put_pickle(self, key, package):
        """Unpickle package and put into the locals namespace with name key."""
        
        d = self.submitCommand(Command("put_pickle", key, package))
        return d
        
    def get(self, key):
        """Gets an item out of the self.locals dict by key."""
        
        d = self.submitCommand(Command("get", key))
        return d

    def get_pickle(self, key):
        """Gets an item out of the self.locals dist by key and pickles it."""

        d = self.submitCommand(Command("get_pickle", key))
        return d

    def reset(self):
        """Reset the InteractiveShell."""
        
        d = self.submitCommand(Command("reset"))
        return d
        
    def get_command(self, i=None):
        """Get the stdin/stdout/stderr of command i."""

        d = self.submitCommand(Command("get_command", i))
        return d

    def get_last_command_index(self):
        """Get the index of the last command."""

        d = self.submitCommand(Command("get_last_command_index"))
        return d

