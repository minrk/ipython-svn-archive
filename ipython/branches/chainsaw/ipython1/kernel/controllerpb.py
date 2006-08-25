# -*- test-case-name: ipython1.test.test_controllerpb -*-
"""A perspective broker interface to the controller"""
import cPickle as pickle

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
        return self.service.verifyTargets(targets).addBoth(pickle.dumps, 2)
    
    def remote_scatter(self, targets, key, pseq, style='basic', flatten=False):
        """partition and distribute a sequence"""
        seq = pickle.loads(pseq)
        d = self.service.scatter(targets, key, seq, style, flatten)
        return d.addBoth(pickle.dumps, 2)
    
    def remote_gather(self, targets, key, style='basic'):
        """gather object as distributed by scatter"""
        d = self.service.gather(targets, key, style)
        return d.addBoth(pickle.dumps, 2)
    
    def remote_pushSerialized(self, targets, pns):
        """Push a dict of keys and Serialized to the user's namespace."""
        d = self.service.pushSerialized(targets, **pickle.loads(pns))
        return d.addBoth(pickle.dumps, 2)
    
    def remote_pullSerialized(self, targets, *keys):
        """Pull objects by key form the user's namespace as Serialized."""
        d = self.service.pullSerialized(targets, *keys)
        return d.addBoth(pickle.dumps, 2)
    
    def remote_clearQueue(self, targets):
        """Clears out pending commands in an engine's queue."""
        return self.service.clearQueue(targets).addBoth(pickle.dumps, 2)
    
    def remote_execute(self, targets, lines):
        """Execute lines of Python code."""
        d = self.service.execute(targets, lines)
        return d.addBoth(pickle.dumps, 2)
    
    def remote_push(self, targets, pns):
        """Push value into locals namespace with name key."""
        d = self.service.push(targets, **pickle.loads(pns))
        return d.addBoth(pickle.dumps, 2)
    
    def remote_pull(self, targets, *keys):
        """Gets an item out of the self.locals dict by key."""
        return self.service.pull(targets, *keys).addBoth(pickle.dumps, 2)
    
    def remote_pullNamespace(self, targets, *keys):
        """Gets a namespace dict from targets by keys."""
        d = self.service.pullNamespace(targets, *keys)
        return d.addBoth(pickle.dumps, 2)
    
    def remote_getResult(self, targets, i=None):
        """Get the stdin/stdout/stderr of command i."""
        return self.service.getResult(targets, i).addBoth(pickle.dumps, 2)
    
    def remote_reset(self, targets):
        """Reset the InteractiveShell."""
        return self.service.reset(targets).addBoth(pickle.dumps, 2)
    
    def remote_status(self, targets):
        """Return the status of engines"""
        return self.service.status(targets).addBoth(pickle.dumps, 2)
    
    def remote_kill(self, targets):
        """Kills the engine process"""
        return self.service.kill(targets).addBoth(pickle.dumps, 2)
    

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
        cs.addAllMethods(self)
    
    def verifyTargets(self, targets):
        """verify if targets is callable id list, id, or string 'all'"""
        return self.callRemote('verifyTargets', targets)
    
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        """partition and distribute a sequence"""
        pseq = pickle.dumps(seq, 2)
        d = self.callRemote('scatter', targets, key, pseq, style, flatten)
        return d.addCallback(pickle.loads)
    
    def gather(self, targets, key, style='basic'):
        """gather object as distributed by scatter"""
        d = self.callRemote('gather', targets, key, style='basic')
        return d.addCallback(pickle.loads)
    
    def pushSerialized(self, targets, **namespace):
        """Push a dict of keys and Serialized to the user's namespace."""
        pns = pickle.dumps(namespace, 2)
        d = self.callRemote('pushSerialized', targets, pns)
        return d.addCallback(pickle.loads)
    
    def pullSerialized(self, targets, *keys):
        """Pull objects by key form the user's namespace as Serialized."""
        d = self.callRemote('pullSerialized', targets, *keys)
        return d.addCallback(pickle.loads)
    
    def clearQueue(self, targets):
        """Clears out pending commands in an engine's queue."""
        d = self.callRemote('clearQueue', targets)
        return d.addCallback(pickle.loads)
    
    def execute(self, targets, lines):
        """Execute lines of Python code."""
        d = self.callRemote('execute', targets, lines)
        return d.addCallback(pickle.loads)
    
    def push(self, targets, **namespace):
        """Push value into locals namespace with name key."""
        pns = pickle.dumps(namespace, 2)
        d = self.callRemote('push', targets, pns)
        return d.addCallback(pickle.loads)
    
    def pull(self, targets, *keys):
        """Gets an item out of the self.locals dict by key."""
        return self.callRemote('pull', targets, *keys).addCallback(pickle.loads)
    
    def pullNamespace(self, targets, *keys):
        """Gets a namespace dict from targets by keys."""
        d = self.callRemote('pullNamespace', targets, *keys)
        return d.addCallback(pickle.loads)
    
    def getResult(self, targets, i=None):
        """Get the stdin/stdout/stderr of command i."""
        d = self.callRemote('getResult', targets, i)
        return d.addCallback(pickle.loads)
    
    def reset(self, targets):
        """Reset the InteractiveShell."""
        d = self.callRemote('reset', targets)
        return d.addCallback(pickle.loads)
    
    def status(self, targets):
        """Return the status of engines"""
        d = self.callRemote('status', targets)
        return d.addCallback(pickle.loads)
    
    def kill(self, targets):
        """Kills the engine process"""
        d = self.callRemote('kill', targets)
        return d.addCallback(pickle.loads)
    

components.registerAdapter(PBRemoteController, pb.RemoteReference, cs.IMultiEngine)