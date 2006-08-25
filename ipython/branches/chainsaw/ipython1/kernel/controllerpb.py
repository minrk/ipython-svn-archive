"""A perspective broker interface to the controller"""
import cPickle as pickle

from twisted.python import components
from twisted.spread import pb
from zope.interface import Interface, implements

from ipython1.kernel import controllerservice as cs, util

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
    
    def remote_scatter(self, targets, key, pseq, style='basic', flatten=False):
        """partition and distribute a sequence"""
        seq = pickle.loads(pseq)
        return self.service.scatter(targets, key, seq, style, flatten)
    
    def remote_scatterAll(self, key, pseq, style='basic', flatten=False):
        """"""
        seq = pickle.loads(pseq)
        return self.service.scatterAll(key, seq, style, flatten)
    
    def remote_gather(self, targets, key, style='basic'):
        """gather object as distributed by scatter"""
        d = self.service.gather(targets, key, style)
        return d.addCallback(pickle.dumps, 2)
    
    def remote_gatherAll(self, key, style='basic'):
        """"""
        return self.service.gatherAll(key, style).addCallback(pickle.dumps, 2)
    
    #IRemoteEngine multiplexer methods
    def remote_pushSerialized(self, targets, pns):
        """Push a dict of keys and Serialized to the user's namespace."""
        return self.service.pushSerialized(targets, **pickle.loads(pns))
    
    def remote_pushSerializedAll(self, pns):
        """Push a dict of keys and Serialized to the user's namespace."""
        return self.service.pushSerializedAll(**pickle.loads(pns))
    
    def remote_pullSerialized(self, targets, *keys):
        """Pull objects by key form the user's namespace as Serialized."""
        d = self.service.pullSerialized(targets, *keys)
        return d.addCallback(pickle.dumps, 2)
    
    def remote_pullSerializedAll(self, *keys):
        """Pull objects by key form the user's namespace as Serialized."""
        d = self.service.pullSerializedAll(*keys)
        return d.addCallback(pickle.dumps, 2)
    
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
        d = self.service.execute(targets, lines)
        return d
    
    def remote_executeAll(self, lines):
        """Execute lines of Python code."""
        return self.service.executeAll(lines)
    
    def remote_push(self, targets, pns):
        """Push value into locals namespace with name key."""
        return self.service.push(targets, **pickle.loads(pns))
    
    def remote_pushAll(self, pns):
        """"""
        return self.service.pushAll(**pickle.loads(pns))
    
    def remote_pull(self, targets, *keys):
        """Gets an item out of the self.locals dict by key."""
        return self.service.pull(targets, *keys).addCallback(pickle.dumps, 2)
    
    def remote_pullAll(self, *keys):
        """"""
        return self.service.pullAll(*keys).addCallback(pickle.dumps, 2)
    
    def remote_pullNamespace(self, targets, *keys):
        """Gets a namespace dict from targets by keys."""
        d = self.service.pullNamespace(targets, *keys)
        return d.addCallback(pickle.dumps, 2)
    
    def remote_pullNamespaceAll(self, *keys):
        """"""
        d = self.service.pullNamespaceAll(*keys)
        return d.addCallback(pickle.dumps, 2)
    
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
        pseq = pickle.dumps(seq, 2)
        return self.callRemote('scatter', targets, key, pseq, style, flatten)
    
    def scatterAll(self, key, seq, style='basic', flatten=False):
        """"""
        pseq = pickle.dumps(seq, 2)
        return self.callRemote('scatterAll', key, pseq, style, flatten)
    
    def gather(self, targets, key, style='basic'):
        """gather object as distributed by scatter"""
        d = self.callRemote('gather', targets, key, style='basic')
        return d.addCallback(pickle.loads)
    
    def gatherAll(self, key, style='basic'):
        """"""
        d = self.callRemote('gatherAll', key, style='basic')
        return d.addCallback(pickle.loads)
    
    #IRemoteEngine multiplexer methods
    def pushSerialized(self, targets, **namespace):
        """Push a dict of keys and Serialized to the user's namespace."""
        sns = {}
        for k,v in namespace.iteritems():
            sns[k] = serialized.serialize(v, k)
        pns = pickle.dumps(sns, 2)
        return self.callRemote('pushSerialized', targets, pns)
    
    def pushSerializedAll(self, **namespace):
        """Push a dict of keys and Serialized to the user's namespace."""
        sns = {}
        for k,v in namespace.iteritems():
            sns[k] = serialized.serialize(v, k)
        pns = pickle.dumps(sns, 2)
        return self.callRemote('pushSerializedAll', pns)
    
    def pullSerialized(self, targets, *keys):
        """Pull objects by key form the user's namespace as Serialized."""
        d = self.callRemote('pullSerialized', targets, *keys)
        return d.addCallback(pickle.loads).addCallback(util.unpack)
    
    def pullSerializedAll(self, *keys):
        """Pull objects by key form the user's namespace as Serialized."""
        d = self.callRemote('pullSerializedAll', *keys)
        return d.addCallback(pickle.loads).addCallback(util.unpack)
    
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
        pns = pickle.dumps(namespace, 2)
        return self.callRemote('push', targets, pns)
    
    def pushAll(self, **namespace):
        """"""
        pns = pickle.dumps(namespace, 2)
        return self.callRemote('pushAll', ppns)
    
    def pull(self, targets, *keys):
        """Gets an item out of the self.locals dict by key."""
        return self.callRemote('pull', targets, *keys).addCallback(pickle.loads)
    
    def pullAll(self, *keys):
        """"""
        return self.callRemote('pullAll', *keys).addCallback(pickle.loads)
    
    def pullNamespace(self, targets, *keys):
        """Gets a namespace dict from targets by keys."""
        d = self.callRemote('pullNamespace', targets, *keys)
        return d.addCallback(pickle.loads)
    
    def pullNamespaceAll(self, *keys):
        """"""
        d = self.callRemote('pullNamespaceAll', *keys)
        return d.addCallback(pickle.loads)
    
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