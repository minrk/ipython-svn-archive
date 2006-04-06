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

    def __init__(self, remote_method, **kwargs):
        self.remote_method = remote_method
        self.kwargs = kwargs
        
    def setDeferred(self, d):
        """Sets the deferred attribute of the Command."""
        self.deferred = d

class KEProcessProtocol(protocol.ProcessProtocol):

    def __init__(self, service):
        self.service = service
        
    def connectionMade(self):
        log.msg("connectionMade()")
        reactor.callLater(2,self.service.connectKernelEngineProcess)
    
    def outReceived(self, data):
        #self.service.outReceived(data)
        log.msg(data)
        
    def errReceivved(self, data):
        #self.service.errReceived(data)
        log.msg(data)
        
    def processEnded(self, status):
        #if isinstance(status.value, ProcessDone):
        log.msg("Kernel Engine Process Completed")
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
        self.queued = []
        self.currentCommand = None
        self.autoStart = True
        self.autoConnect = True
        self.rootObject = None

    #def outReceived(self, data);
    #    log.msg(data)
     
    #def errReceived(self, data);
    #    log.msg(data)   

    def startService(self):
        service.Service.startService(self)
        reactor.callLater(5,self.startKernelEngineProcess)
        
    def startKernelEngineProcess(self):
        self.KEProtocol = KEProcessProtocol(self)
        reactor.spawnProcess(self.KEProtocol,
            'ipengine',
            args=['ipengine','-p %i' % self.port],
            env = os.environ)
        
    def stopKernelEngineProcess(self):
        os.kill(self.KEProtocol.transport.pid, signal.SIGKILL)
    
    #def restartKernelEngineProcess(self, port):
    #    self.self.autoStart = True
    #    self.killKernelEngineProcess()
        
    def connectKernelEngineProcess(self):
        self.KEFactory = pb.PBClientFactory()
        reactor.connectTCP("127.0.0.1", self.port, self.KEFactory)
        self.KEFactory.getRootObject().addCallbacks(self.gotRoot,
                                                    self.gotNoRoot)
                                                                                   
    def gotRoot(self, obj):
        self.rootObject = obj
        log.msg("Got the root object!")
        
    def gotNoRoot(self, reason):
        reason.printDetailedTraceback()

    def disconnectKernelEngineProcess(self):
        self.KEFactory.disconnect()

    #def submitCommand(cmd):
    #    
    #    print "Submitting: ", cmd
    #    d = defer.Deferred()
    #    d.addCallback(self.finalizeCommand)
    #    d.addErrback(self.abortCommand)
    #    cmd.setDeferred(d)
    #    if self.currentCommand is not None:
    #        print "Queueing: ", cmd
    #        self.queued.append(cmd)
    #        return d
    #    print "Starting: ", cmd
    #    self.currentCommand = cmd
    #    self.currentCommand.sendInitial()
    #
    #    return d
    

    # Methods that should use the queue

    #def execute(self, lines):
    #    """Execute lines of Python code."""
    #    d = self.submit_command(Command("execute", lines))
    #    return d
        


    
    
    
