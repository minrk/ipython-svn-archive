"""A Twisted Service Representation of the IPython Core"""

import os, signal

from twisted.application import internet, service
from twisted.internet import protocol, reactor, defer
from twisted.python import components, log
from twisted.web import xmlrpc
from zope.interface import Interface, implements

from twisted.spread import pb

import cPickle as pickle

from ipython1.core.shell import InteractiveShell

# Here is the interface specification for the IPythonCoreService

class ICoreService(Interface):
    """The Interface for the IPython Core"""
    
    def execute(self, lines):
        """Execute lines of Python code."""
    
    def put(self, key, value):
        """Put value into locals namespace with name key."""
        
    def put_pickle(self, key, package):
        """Unpickle package and put into the locals namespace with name key."""
        
    def get(self, key):
        """Gets an item out of the self.locals dict by key."""

    def get_pickle(self, key):
        """Gets an item out of the self.locals dist by key and pickles it."""

    def reset(self):
        """Reset the InteractiveShell."""
        
    def get_command(self, i=None):
        """Get the stdin/stdout/stderr of command i."""

    def get_last_command_index(self):
        """Get the index of the last command."""

# Now the actual CoreService implementation                   

class CoreService(service.Service):

    implements(ICoreService)
    
    def __init__(self, ):
        self.ishell = InteractiveShell()
                
    def execute(self, lines):
        log.msg("execute: %s" % lines)
        return defer.succeed(self.ishell.execute(lines))
    
    def put(self, key, value):
        log.msg("put: %s" % key)
        return defer.succeed(self.ishell.put(key, value))
        
    def put_pickle(self, key, package):
        log.msg("put_pickle: %s" % key)    
        try:
            value = pickle.loads(package)
        except pickle.PickleError:
            return defer.fail()
        else:
            return defer.succeed(self.ishell.put(key, value))
        
    def get(self, key):
        log.msg("get: %s" % key)
        return defer.succeed(self.ishell.get(key))

    def get_pickle(self, key):
        log.msg("get_pickle: %s" % key)
        value = self.ishell.get(key)
        try:
            package = pickle.dumps(value, 2)
        except pickle.PickleError:
            return defer.fail()
        else:
            return defer.succeed(package)

    def reset(self):
        log.msg("reset")
        return defer.succeed(self.ishell.reset())
        
    def get_command(self, i=None):
        log.msg("get_command: %i" % i)
        return defer.succeed(self.ishell.get_command(i))

    def get_last_command_index(self):
        log.msg("get_last_command_index:")
        return defer.succeed(self.ishell.get_last_command_index())
     
# Expose a PB interface to the CoreService
     
class IPerspectiveCore(Interface):

    def remote_execute(self, lines):
        """Execute lines of Python code."""
    
    def remote_put(self, key, value):
        """Put value into locals namespace with name key."""
        
    def remote_put_pickle(self, key, package):
        """Unpickle package and put into the locals namespace with name key."""
        
    def remote_get(self, key):
        """Gets an item out of the self.locals dict by key."""

    def remote_get_pickle(self, key):
        """Gets an item out of the self.locals dist by key and pickles it."""

    def remote_reset(self):
        """Reset the InteractiveShell."""
        
    def remote_get_command(self, i=None):
        """Get the stdin/stdout/stderr of command i."""

    def remote_get_last_command_index(self):
        """Get the index of the last command."""

class PerspectiveCoreFromService(pb.Root):

    implements(IPerspectiveCore)

    def __init__(self, service):
        self.service = service

    def remote_execute(self, lines):
        return self.service.execute(lines)
    
    def remote_put(self, key, value):
        return self.service.put(key, value)
        
    def remote_put_pickle(self, key, package):
        return self.service.put_pickle(key, package)
        
    def remote_get(self, key):
        return self.service.get(key)

    def remote_get_pickle(self, key):
        return self.service.get_pickle(key)

    def remote_reset(self):
        return self.service.reset()
        
    def remote_get_command(self, i=None):
        return self.service.get_command(i)

    def remote_get_last_command_index(self):
        return self.service.get_last_command_index()
    
components.registerAdapter(PerspectiveCoreFromService,
                           CoreService,
                           IPerspectiveCore)
           
# Classes for the Kernel Engine

class Command(object):

    def __init__(self, remoteMethod, *args):
        self.remoteMethod = remoteMethod
        self.args = args
        
    def setDeferred(self, d):
        """Sets the deferred attribute of the Command."""
        self.deferred = d

    def __repr__(self):
        return "Command: " + self.remoteMethod + repr(self.args)
        
    def handleResult(self, result):
        log.msg("Handling Result: " + repr(result))
        self.deferred.callback(result)
        
    def handleError(self, reason):
        self.deferred.errback(reason)

class KEProcessProtocol(protocol.ProcessProtocol):

    def __init__(self, service):
        self.service = service
        
    def connectionMade(self):
        """Called when the Ke process is running.
        
        This should immediately trigger connecting to the KE process
        over a socket.
        """
        
        # We need to make sure that the kernel engine has really started
        # before connecting to it
        reactor.callLater(1,self.service.connectKernelEngineProcess)
    
    def outReceived(self, data):
        self.service.outReceived(data)
                
    def errReceivved(self, data):
        self.service.errReceived(data)
        
    def processEnded(self, status):
        self.service.handleKEProcessEnding(status)
        #if isinstance(status.value, ProcessDone):
        #log.msg("Kernel Engine Process Completed")
        #else isinstance(status.value, ProcessTerminated):
        #    log.msg("Kernel Engine Process Died")
        #self.service.maybeRestartKernelEngineProcess()
           
class IKernelEngineService(ICoreService):
    """Adds a few controll methods to the IPythonCoreService API"""
    
    def restart(self):
        """Restart the IPython Kernel Engine"""
        
    def clean_queue(self):
        """Remove pending commands."""

class KernelEngineService(service.Service):

    #implements(IIPythonEngineService)
    
    def __init__(self, port):
        
        self.port = port
        self.autoStart = True
        self.rootObject = None
        self.KEFactory = None
        self.queued = []
        self.currentCommand = None
        
    def outReceived(self, data):
        """Called when the KE process writes to stdout."""
        log.msg(data)
     
    def errReceived(self, data):
        """Called when the KE process writes to stdout."""
        log.msg(data)   

    # Methods to manage the Kernel Engine Process 

    def startService(self):
        service.Service.startService(self)
        # I seem to need this to ensure the reactor is running before
        # spawnProcess is called
        reactor.callLater(0.1,self.startKernelEngineProcess)
        #reactor.callLater(10,self.restartKernelEngineProcess)
        
    def startKernelEngineProcess(self):
        self.KEProtocol = KEProcessProtocol(self)
        reactor.spawnProcess(self.KEProtocol,
            'ipengine',
            args=['ipengine','-p %i' % self.port],
            env = os.environ)
        self.autoStart = True  # autoStart by default
        
    def stopKernelEngineProcess(self):
        self.autoStart = False   # Don't restart automatically after killing
        self.disconnectKernelEngineProcess()
        os.kill(self.KEProtocol.transport.pid, signal.SIGKILL)

    def restartKernelEngineProcess(self):
        self.autoStart = True
        self.disconnectKernelEngineProcess()
        os.kill(self.KEProtocol.transport.pid, signal.SIGKILL)

    def handleKEProcessEnding(self, status):
        """Called when the KE process ends.  Decides whether to restart.
        
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
        self.KEFactory = pb.PBClientFactory()
        reactor.connectTCP("127.0.0.1", self.port, self.KEFactory)
        self.KEFactory.getRootObject().addCallbacks(self.gotRoot,
                                                    self.gotNoRoot)
                                                                                   
    def gotRoot(self, obj):
        self.rootObject = obj
        log.msg("Connected to the Kernel Engine.")
        self.testCommands()
        
    def testCommands(self):

        d = self.execute("import time")
        d.addCallback(self.printer)
        d = self.execute("time.sleep(10)")
        d.addCallback(self.printer)        
        
        d = self.execute("a = 5")
        d.addCallback(self.printer)
        d = self.execute("b = 10")
        d.addCallback(self.printer)
        d = self.execute("c = a + b")
        d.addCallback(self.printer)
        d = self.execute("print c")
        d.addCallback(self.printer)
        
    def printer(self, stuff):
        print stuff
        
    def gotNoRoot(self, reason):
        reason.printDetailedTraceback()

    def disconnectKernelEngineProcess(self):
        if self.KEFactory:
            self.KEFactory.disconnect()
        self.rootObject = None
        self.KEFactory = None

    # The logic of the service

    def submitCommand(self, cmd):
        
        log.msg("Submitting: " + repr(cmd))
        d = defer.Deferred()
        cmd.setDeferred(d)
        if self.currentCommand is not None:
            log.msg("Queueing: " + repr(cmd))
            self.queued.append(cmd)
            return d
        log.msg("Starting: " + repr(cmd))
        self.currentCommand = cmd
        self.runCurrentCommand()
    
        return d
    
    def runCurrentCommand(self):
        cmd = self.currentCommand
        d = self.rootObject.callRemote(cmd.remoteMethod, *(cmd.args))
        d.addCallback(self.finalizeCommand)
        d.addErrback(self.abortCommand)

    def _flushQueue(self):
 
        if len(self.queued) > 0:
            self.currentCommand = self.queued.pop(0)
            log.msg("Starting: " + repr(self.currentCommand))
            self.runCurrentCommand()

    def finalizeCommand(self, result):
        log.msg("Finalizing: " + repr(self.currentCommand) + repr(result))
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
        return reason

    # Methods that should use the queue

    def execute(self, lines):
        """Execute lines of Python code."""
        d = self.submitCommand(Command("execute", lines))
        return d
        


    
    
    
