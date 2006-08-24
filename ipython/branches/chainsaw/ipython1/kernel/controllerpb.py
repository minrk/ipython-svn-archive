"""A perspective broker interface to the controller"""

from twisted.python import components
from twisted.spread import pb
from zope.interface import Interface, implements

from ipython1.kernel import controllerservice as cs

class IPBController(Interface):
    """Perspective Broker interface to controller.  Same as IMultiEngine, but
    with 'remote_'
    """
    
    def remote_verifyTargets(targets):
        """verify if targets is callable id list, id, or string 'all'"""
    
    def remote_scatter(targets, key, seq, style='basic', flatten=False):
        """partition and distribute a sequence"""
    
    def remote_scatterAll(key, seq, style='basic', flatten=False):
        """"""
    
    def remote_gather(targets, key, style='basic'):
        """gather object as distributed by scatter"""
    
    def remote_gatherAll(key, style='basic'):
        """"""
    
    #IRemoteEngine multiplexer methods
    def remote_pushSerialized(targets, **namespace):
        """Push a dict of keys and Serialized to the user's namespace."""
    
    def remote_pushSerializedAll(**namespace):
        """Push a dict of keys and Serialized to the user's namespace."""
    
    def remote_pullSerialized(targets, *keys):
        """Pull objects by key form the user's namespace as Serialized."""
    
    def remote_pullSerializedAll(*keys):
        """Pull objects by key form the user's namespace as Serialized."""
    
    #IQueuedEngine multiplexer methods
    def remote_clearQueue(targets):
        """Clears out pending commands in an engine's queue."""
    
    def remote_clearQueueAll():
        """Clears out pending commands in all queues."""
    
    #IEngineCompleteBase multiplexer methods
    def remote_execute(targets, lines):
        """Execute lines of Python code."""
    
    def remote_executeAll(lines):
        """Execute lines of Python code."""
    
    def remote_push(targets, **namespace):
        """Push value into locals namespace with name key."""
    
    def remote_pushAll(**namespace):
        """"""
    
    def remote_pull(targets, *keys):
        """Gets an item out of the self.locals dict by key."""
    
    def remote_pullAll(*keys):
        """"""
    
    def remote_pullNamespace(targets, *keys):
        """Gets a namespace dict from targets by keys."""
    
    def remote_pullNamespaceAll(*keys):
        """"""
    
    def remote_getResult(targets, i=None):
        """Get the stdin/stdout/stderr of command i."""
    
    def remote_getResultAll(i=None):
        """"""
    
    def remote_reset(targets):
        """Reset the InteractiveShell."""
    
    def remote_resetAll():
        """"""
    
    def remote_status(targets):
        """Return the status of engines"""
    
    def remote_statusAll():
        """"""
    
    def remote_kill(targets):
        """Kills the engine process"""
    
    def remote_killAll():
        """"""
    


#implementation if IPBController
class PBControllerRootFromService(pb.Root):
    """Perspective Broker interface to controller.  Same as IMultiEngine, but
    with 'remote_'
    """
    implements(IPBController)
    
    def __init__(self, cs):
        self.service = cs
    
    def remote_verifyTargets(self, targets):
        """verify if targets is callable id list, id, or string 'all'"""
        return self.service.verifyTargets(targets)
    
    def remote_scatter(self, targets, key, seq, style='basic', flatten=False):
        """partition and distribute a sequence"""
        return self.service.scatter(targets, key, seq, style, flatten)
    
    def remote_scatterAll(self, key, seq, style='basic', flatten=False):
        """"""
        return self.service.scatterAll(key, seq, style, flatten)
    
    def remote_gather(self, targets, key, style='basic'):
        """gather object as distributed by scatter"""
        return self.service.gather(targets, key, style)
    
    def remote_gatherAll(self, key, style='basic'):
        """"""
        return self.service.gatherAll(key, style)
    
    #IRemoteEngine multiplexer methods
    def remote_pushSerialized(self, targets, **namespace):
        """Push a dict of keys and Serialized to the user's namespace."""
        return self.service.pushSerialized(targets, **namespace)
    
    def remote_pushSerializedAll(self, **namespace):
        """Push a dict of keys and Serialized to the user's namespace."""
        return self.service.pushSerializedAll(**namespace)
    
    def remote_pullSerialized(self, targets, *keys):
        """Pull objects by key form the user's namespace as Serialized."""
        return self.service.pullSerialized(targets, *keys)
    
    def remote_pullSerializedAll(self, *keys):
        """Pull objects by key form the user's namespace as Serialized."""
        return self.service.pullSerializedAll(*keys)
    
    #IQueuedEngine multiplexer methods
    def remote_clearQueue(self, targets):
        """Clears out pending commands in an engine's queue."""
        return self.service.clearQueue(targets)
    
    def remote_clearQueueAll(self):
        """Clears out pending commands in all queues."""
        return self.service.clearQueueAll()
    
    #IEngineCompleteBase multiplexer methods
    def remote_execute(self, targets, lines):
        """Execute lines of Python code."""
        return self.service.execute(targets, lines)
    
    def remote_executeAll(self, lines):
        """Execute lines of Python code."""
        return self.service.executeAll(lines)
    
    def remote_push(self, targets, **namespace):
        """Push value into locals namespace with name key."""
        return self.service.push(targets, **namespace)
    
    def remote_pushAll(self, **namespace):
        """"""
        return self.service.pushAll(**namespace)
    
    def remote_pull(self, targets, *keys):
        """Gets an item out of the self.locals dict by key."""
        return self.service.pull(targets, *keys)
    
    def remote_pullAll(self, *keys):
        """"""
        return self.service.pullAll(*keys)
    
    def remote_pullNamespace(self, targets, *keys):
        """Gets a namespace dict from targets by keys."""
        return self.service.pullNamespace(targets, *keys)
    
    def remote_pullNamespaceAll(self, *keys):
        """"""
        return self.service.pullNamespaceAll(*keys)
    
    def remote_getResult(self, targets, i=None):
        """Get the stdin/stdout/stderr of command i."""
        return self.service.getResult(targets, i)
    
    def remote_getResultAll(self, i=None):
        """"""
        return self.service.getResultAll(i)
    
    def remote_reset(self, targets):
        """Reset the InteractiveShell."""
        return self.service.reset(targets)
    
    def remote_resetAll(self):
        """"""
        return self.service.resetAll()
    
    def remote_status(self, targets):
        """Return the status of engines"""
        return self.service.status(targets)
    
    def remote_statusAll(self):
        """"""
        return self.service.statusAll()
    
    def remote_kill(self, targets):
        """Kills the engine process"""
        return self.service.kill(targets)
    
    def remote_killAll(self):
        """"""
        return self.service.killAll()
    

components.registerAdapter(PBControllerRootFromService,
            cs.ControllerService, IPBController)



#END stuff that goes on the controller

#BEGIN counterparts

class PBRemoteController(object):
    """remote controller object, connected through perspective broker
    """
    implements(cs.IMultiEngine)
    
    def __init__(self, reference):
        self.reference = reference
        self.callRemote = reference.callRemote
    
    def verifyTargets(self, targets):
        """verify if targets is callable id list, id, or string 'all'"""
        return self.callRemote('verifyTargets', targets)
    
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        """partition and distribute a sequence"""
        return self.callRemote('scatter', targets, key, seq, style, flatten)
    
    def scatterAll(self, key, seq, style='basic', flatten=False):
        """"""
        return self.callRemote('scatterAll', key, seq, style, flatten)
    
    def gather(self, targets, key, style='basic'):
        """gather object as distributed by scatter"""
        return self.callRemote('gather', targets, key, style='basic')
    
    def gatherAll(self, key, style='basic'):
        """"""
        return self.callRemote('gatherAll', key, style='basic')
    #IRemoteEngine multiplexer methods
    def pushSerialized(self, targets, **namespace):
        """Push a dict of keys and Serialized to the user's namespace."""
        return self.callRemote('pushSerialized', targets, **namespace)
    
    def pushSerializedAll(self, **namespace):
        """Push a dict of keys and Serialized to the user's namespace."""
        return self.callRemote('pushSerializedAll', **namespace)
    
    def pullSerialized(self, targets, *keys):
        """Pull objects by key form the user's namespace as Serialized."""
        return self.callRemote('pullSerialized', targets, *keys)
    
    def pullSerializedAll(self, *keys):
        """Pull objects by key form the user's namespace as Serialized."""
        return self.callRemote('pullSerializedAll', *keys)
    
    #IQueuedEngine multiplexer methods
    def clearQueue(self, targets):
        """Clears out pending commands in an engine's queue."""
        return self.callRemote('clearQueue', targets)
    
    def clearQueueAll(self):
        """Clears out pending commands in all queues."""
        return self.callRemote('clearQueueAll')
    
    #IEngineCompleteBase multiplexer methods
    def execute(self, targets, lines):
        """Execute lines of Python code."""
        return self.callRemote('execute', targets, lines)
    
    def executeAll(self, lines):
        """Execute lines of Python code."""
        return self.callRemote('executeAll', lines)
    
    def push(self, targets, **namespace):
        """Push value into locals namespace with name key."""
        return self.callRemote('push', targets, **namespace)
    
    def pushAll(self, **namespace):
        """"""
        return self.callRemote('pushAll', **namespace)
    
    def pull(self, targets, *keys):
        """Gets an item out of the self.locals dict by key."""
        return self.callRemote('pull', targets, *keys)
    
    def pullAll(self, *keys):
        """"""
        return self.callRemote('pullAll', *keys)
    
    def pullNamespace(self, targets, *keys):
        """Gets a namespace dict from targets by keys."""
        return self.callRemote('pullNamespace', targets, *keys)
    
    def pullNamespaceAll(self, *keys):
        """"""
        return self.callRemote('pullNamespaceAll', *keys)
    
    def getResult(self, targets, i=None):
        """Get the stdin/stdout/stderr of command i."""
        return self.callRemote('getResult', targets, i)
    
    def getResultAll(self, i=None):
        """"""
        return self.callRemote('getResultAll', i)
    
    def reset(self, targets):
        """Reset the InteractiveShell."""
        return self.callRemote('reset', targets)
    
    def resetAll(self):
        """"""
        return self.callRemote('resetAll')
    
    def status(self, targets):
        """Return the status of engines"""
        return self.callRemote('status', targets)
    
    def statusAll(self):
        """"""
        return self.callRemote('statusAll')
    
    def kill(self, targets):
        """Kills the engine process"""
        return self.callRemote('kill', targets)
    
    def killAll(self):
        """"""
        return self.callRemote('killAll')
    

components.registerAdapter(PBRemoteController, pb.RemoteReference, cs.IMultiEngine)