# -*- test-case-name: ipython1.test.test_controllerpb -*-
"""A perspective broker interface to the controller"""
import cPickle as pickle

from twisted.python import components
from twisted.spread import pb
from zope.interface import Interface, implements

from ipython1.kernel import controllerservice as cs, util, serialized

class IPBController(Interface):
    """Perspective Broker interface to controller.  Same as IMultiEngine, but
    with 'remote_'
    """
    
    def remote_verifyTargets(targets):
        """verify if targets is callable id list, id, or string 'all'"""
    
    def remote_scatter(targets, key, seq, style='basic', flatten=False):
        """partition and distribute a sequence"""
    
    def remote_gather(targets, key, style='basic'):
        """gather object as distributed by scatter"""
    
    #IRemoteEngine multiplexer methods
    def remote_pushSerialized(targets, **namespace):
        """Push a dict of keys and Serialized to the user's namespace."""
    
    def remote_pullSerialized(targets, *keys):
        """Pull objects by key form the user's namespace as Serialized."""
    
    #IQueuedEngine multiplexer methods
    def remote_clearQueue(targets):
        """Clears out pending commands in an engine's queue."""
    
    #IEngineCompleteBase multiplexer methods
    def remote_execute(targets, lines):
        """Execute lines of Python code."""
    
    def remote_push(targets, **namespace):
        """Push value into locals namespace with name key."""
    
    def remote_pull(targets, *keys):
        """Gets an item out of the self.locals dict by key."""
    
    def remote_pullNamespace(targets, *keys):
        """Gets a namespace dict from targets by keys."""
    
    def remote_getResult(targets, i=None):
        """Get the stdin/stdout/stderr of command i."""
    
    def remote_reset(targets):
        """Reset the InteractiveShell."""
    
    def remote_status(targets):
        """Return the status of engines"""
    
    def remote_kill(targets):
        """Kills the engine process"""
    

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
    
    def remote_gather(self, targets, key, style='basic'):
        """gather object as distributed by scatter"""
        d = self.service.gather(targets, key, style)
        return d.addCallback(pickle.dumps, 2)
    
    def remote_pushSerialized(self, targets, pns):
        """Push a dict of keys and Serialized to the user's namespace."""
        return self.service.pushSerialized(targets, **pickle.loads(pns))
    
    def remote_pullSerialized(self, targets, *keys):
        """Pull objects by key form the user's namespace as Serialized."""
        d = self.service.pullSerialized(targets, *keys)
        return d.addCallback(pickle.dumps, 2)
    
    def remote_clearQueue(self, targets):
        """Clears out pending commands in an engine's queue."""
        return self.service.clearQueue(targets)
    
    def remote_execute(self, targets, lines):
        """Execute lines of Python code."""
        d = self.service.execute(targets, lines)
        return d
    
    def remote_push(self, targets, pns):
        """Push value into locals namespace with name key."""
        return self.service.push(targets, **pickle.loads(pns))
    
    def remote_pull(self, targets, *keys):
        """Gets an item out of the self.locals dict by key."""
        return self.service.pull(targets, *keys).addCallback(pickle.dumps, 2)
    
    def remote_pullNamespace(self, targets, *keys):
        """Gets a namespace dict from targets by keys."""
        d = self.service.pullNamespace(targets, *keys)
        return d.addCallback(pickle.dumps, 2)
    
    def remote_getResult(self, targets, i=None):
        """Get the stdin/stdout/stderr of command i."""
        return self.service.getResult(targets, i)
    
    def remote_reset(self, targets):
        """Reset the InteractiveShell."""
        return self.service.reset(targets)
    
    def remote_status(self, targets):
        """Return the status of engines"""
        return self.service.status(targets)
    
    def remote_kill(self, targets):
        """Kills the engine process"""
        return self.service.kill(targets)
    

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
        return self.callRemote('scatter', 'all', key, pseq, style, flatten)
    
    def gather(self, targets, key, style='basic'):
        """gather object as distributed by scatter"""
        d = self.callRemote('gather', targets, key, style='basic')
        return d.addCallback(pickle.loads)
    
    def gatherAll(self, key, style='basic'):
        """"""
        d = self.callRemote('gather', 'all', key, style='basic')
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
        return self.callRemote('pushSerialized', 'all', pns)
    
    def pullSerialized(self, targets, *keys):
        """Pull objects by key form the user's namespace as Serialized."""
        d = self.callRemote('pullSerialized', targets, *keys)
        return d.addCallback(pickle.loads).addCallback(util.unpack)
    
    def pullSerializedAll(self, *keys):
        """Pull objects by key form the user's namespace as Serialized."""
        d = self.callRemote('pullSerialized', 'all', *keys)
        return d.addCallback(pickle.loads).addCallback(util.unpack)
    
    #IQueuedEngine multiplexer methods
    def clearQueue(self, targets):
        """Clears out pending commands in an engine's queue."""
        return self.callRemote('clearQueue', targets)
    
    def clearQueueAll(self):
        """Clears out pending commands in all queues."""
        return self.callRemote('clearQueue', 'all')
    
    #IEngineCompleteBase multiplexer methods
    def execute(self, targets, lines):
        """Execute lines of Python code."""
        return self.callRemote('execute', targets, lines)
    
    def executeAll(self, lines):
        """Execute lines of Python code."""
        return self.callRemote('execute', 'all', lines)
    
    def push(self, targets, **namespace):
        """Push value into locals namespace with name key."""
        pns = pickle.dumps(namespace, 2)
        return self.callRemote('push', targets, pns)
    
    def pushAll(self, **namespace):
        """"""
        pns = pickle.dumps(namespace, 2)
        return self.callRemote('push', 'all', ppns)
    
    def pull(self, targets, *keys):
        """Gets an item out of the self.locals dict by key."""
        return self.callRemote('pull', targets, *keys).addCallback(pickle.loads)
    
    def pullAll(self, *keys):
        """"""
        return self.callRemote('pull', 'all', *keys).addCallback(pickle.loads)
    
    def pullNamespace(self, targets, *keys):
        """Gets a namespace dict from targets by keys."""
        d = self.callRemote('pullNamespace', targets, *keys)
        return d.addCallback(pickle.loads)
    
    def pullNamespaceAll(self, *keys):
        """"""
        d = self.callRemote('pullNamespace', 'all', *keys)
        return d.addCallback(pickle.loads)
    
    def getResult(self, targets, i=None):
        """Get the stdin/stdout/stderr of command i."""
        return self.callRemote('getResult', targets, i)
    
    def getResultAll(self, i=None):
        """"""
        return self.callRemote('getResult', 'all', i)
    
    def reset(self, targets):
        """Reset the InteractiveShell."""
        return self.callRemote('reset', targets)
    
    def resetAll(self):
        """"""
        return self.callRemote('reset', 'all')
    
    def status(self, targets):
        """Return the status of engines"""
        return self.callRemote('status', targets)
    
    def statusAll(self):
        """"""
        return self.callRemote('status', 'all')
    
    def kill(self, targets):
        """Kills the engine process"""
        return self.callRemote('kill', targets)
    
    def killAll(self):
        """"""
        return self.callRemote('kill', 'all')
    

components.registerAdapter(PBRemoteController, pb.RemoteReference, cs.IMultiEngine)