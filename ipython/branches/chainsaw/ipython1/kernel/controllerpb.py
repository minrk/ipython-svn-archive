# -*- test-case-name: ipython1.test.test_controllerpb -*-
"""A perspective broker interface to the controller"""
import cPickle as pickle

from twisted.python import components, log
from twisted.python.failure import Failure
from twisted.spread import pb
from zope.interface import Interface, implements

from ipython1.kernel import controllerservice as cs, results

class IPBController(Interface):
    """Perspective Broker interface to controller.  Same as IMultiEngine, but
    with 'remote_'
    """
    
    def remote_verifyTargets(targets):
        """verify if targets is callable id list, id, or string 'all'"""
    
    def remote_getIDs():
        """return the currently registered ids"""
    
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
    
    def remote_addNotifier(reference):
        """adds a notifier"""
    

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
    
    def remote_getIDs(self):
        return self.service.getIDs()
    
    def remote_scatter(self, targets, key, pseq, style='basic', flatten=False):
        """partition and distribute a sequence"""
        seq = pickle.loads(pseq)
        d = self.service.scatter(targets, key, seq, style, flatten)
        return d.addErrback(pickle.dumps, 2)
    
    def remote_gather(self, targets, key, style='basic'):
        """gather object as distributed by scatter"""
        d = self.service.gather(targets, key, style)
        return d.addBoth(pickle.dumps, 2)
    
    def remote_pushSerialized(self, targets, pns):
        """Push a dict of keys and Serialized to the user's namespace."""
        d = self.service.pushSerialized(targets, **pickle.loads(pns))
        return d.addErrback(pickle.dumps, 2)
    
    def remote_pullSerialized(self, targets, *keys):
        """Pull objects by key form the user's namespace as Serialized."""
        d = self.service.pullSerialized(targets, *keys)
        return d.addBoth(pickle.dumps, 2)
    
    def remote_clearQueue(self, targets):
        """Clears out pending commands in an engine's queue."""
        return self.service.clearQueue(targets).addErrback(pickle.dumps, 2)
    
    def remote_execute(self, targets, lines):
        """Execute lines of Python code."""
        d = self.service.execute(targets, lines)
        return d.addErrback(pickle.dumps, 2)
    
    def remote_push(self, targets, pns):
        """Push value into locals namespace with name key."""
        d = self.service.push(targets, **pickle.loads(pns))
        return d.addErrback(pickle.dumps, 2)
    
    def remote_pull(self, targets, *keys):
        """Gets an item out of the self.locals dict by key."""
        return self.service.pull(targets, *keys).addBoth(pickle.dumps, 2)
    
    def remote_pullNamespace(self, targets, *keys):
        """Gets a namespace dict from targets by keys."""
        d = self.service.pullNamespace(targets, *keys)
        return d.addBoth(pickle.dumps, 2)
    
    def remote_getResult(self, targets, i=None):
        """Get the stdin/stdout/stderr of command i."""
        d = self.service.getResult(targets, i).addCallback(self.checkReturns)
        return d.addErrback(pickle.dumps, 2)
    
    def remote_reset(self, targets):
        """Reset the InteractiveShell."""
        return self.service.reset(targets).addErrback(pickle.dumps, 2)
    
    def remote_status(self, targets):
        """Return the status of engines"""
        return self.service.status(targets).addErrback(pickle.dumps, 2)
    
    def remote_kill(self, targets):
        """Kills the engine process"""
        return self.service.kill(targets).addErrback(pickle.dumps, 2)
    
    def remote_addNotifier(self, reference):
        """adds a notifier"""
        return self.service.addNotifier(reference)
    
    assert remote_addNotifier
    def checkReturns(self, rlist):
        for r in rlist:
            if isinstance(r, (Failure, Exception)):
                rlist[rlist.index(r)] = pickle.dumps(r, 2)
        return rlist

components.registerAdapter(PBControllerRootFromService,
            cs.ControllerService, IPBController)

class IPBControllerFactory(Interface):
    pass
    
def PBServerFactoryFromService(service):
    return pb.PBServerFactory(IPBController(service))
    
components.registerAdapter(PBServerFactoryFromService,
            cs.ControllerService, IPBControllerFactory)
        

#END stuff that goes on the controller

#BEGIN counterparts

class PBRemoteController(pb.Referenceable):
    """remote controller object, connected through perspective broker
    """
    implements(cs.IMultiEngine)
    
    def __init__(self, reference):
        self.reference = reference
        self.callRemote = reference.callRemote
        cs.addAllMethods(self)
        self.deferred = self.callRemote('addNotifier', self)
    
    def remote_notify(self, result):
        """This should be overridden to be useful"""
        log.msg(result)
    
    def verifyTargets(self, targets):
        """verify if targets is callable id list, id, or string 'all'"""
        d = self.callRemote('verifyTargets', targets)
        return d.addCallback(self.checkReturn)
    
    def getIDs(self):
        """get ids"""
        d = self.callRemote('getIDs', targets)
        return d.addCallback(self.checkReturn)
    
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        """partition and distribute a sequence"""
        pseq = pickle.dumps(seq, 2)
        d = self.callRemote('scatter', targets, key, pseq, style, flatten)
        return d.addCallback(self.checkReturn)
    
    def gather(self, targets, key, style='basic'):
        """gather object as distributed by scatter"""
        d = self.callRemote('gather', targets, key, style='basic')
        return d.addCallback(pickle.loads)
    
    def pushSerialized(self, targets, **namespace):
        """Push a dict of keys and Serialized to the user's namespace."""
        pns = pickle.dumps(namespace, 2)
        d = self.callRemote('pushSerialized', targets, pns)
        return d.addCallback(self.checkReturn)
    
    def pullSerialized(self, targets, *keys):
        """Pull objects by key form the user's namespace as Serialized."""
        d = self.callRemote('pullSerialized', targets, *keys)
        return d.addCallback(pickle.loads)
    
    def clearQueue(self, targets):
        """Clears out pending commands in an engine's queue."""
        d = self.callRemote('clearQueue', targets)
        return d.addCallback(self.checkReturn)
    
    def execute(self, targets, lines):
        """Execute lines of Python code."""
        d = self.callRemote('execute', targets, lines)
        return d.addCallback(self.checkReturn)
    
    def push(self, targets, **namespace):
        """Push value into locals namespace with name key."""
        pns = pickle.dumps(namespace, 2)
        d = self.callRemote('push', targets, pns)
        return d.addCallback(self.checkReturn)
    
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
        return d.addCallback(self.checkReturn)
    
    def reset(self, targets):
        """Reset the InteractiveShell."""
        d = self.callRemote('reset', targets)
        return d.addCallback(self.checkReturn)
    
    def status(self, targets):
        """Return the status of engines"""
        d = self.callRemote('status', targets)
        return d.addCallback(self.checkReturn)
    
    def kill(self, targets):
        """Kills the engine process"""
        d = self.callRemote('kill', targets)
        return d.addCallback(self.checkReturn)
    
    def checkReturn(self, r):
        if isinstance(r, str):
            try: 
                return pickle.loads(r)
            except pickle.PickleError, TypeError: 
                pass
        elif isinstance(r, list):
            return map(self.checkReturn, r)
        return r

    
class PBNotifier(results.BaseNotifier):
    
    def __init__(self, reference):
        self.key = repr(reference)
        self.callRemote = reference.callRemote
        reference.broker.notifyOnDisconnect(self.onDisconnect)
    
    def notify(self, result):
        return self.callRemote('notify', result).addErrback(self.onDisconnect)
    
components.registerAdapter(PBRemoteController, pb.RemoteReference, cs.IMultiEngine)
components.registerAdapter(PBNotifier, pb.RemoteReference, results.INotifier)
