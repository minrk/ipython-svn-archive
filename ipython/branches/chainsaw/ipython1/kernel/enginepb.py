"""Expose the IPython Kernel Service using Twisted's Perspective Broker.

This module specifies the IPBEngineFromService Interface and its implementation
as an Adapter from the IEngineService Interface.  This adapter wraps
EngineService instance into something that inherits from pb.Referenceable.  This makes
is callable using Perspective Broker.

Any public methods of the IKernelService Interface that should be available over
PB must be added to both the Interface and Adapter in this file.

This module must be imported in its entirety to have its Adapters registered
properly:

from ipython1.kernel import enginepb
"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import time
import cPickle as pickle

from twisted.python import components, log
from twisted.spread import pb
from twisted.internet import defer, reactor
from zope.interface import Interface, implements

from ipython1.kernel.engineservice import EngineService, IEngine
from ipython1.kernel.engineservice import QueuedEngine,Command
from ipython1.kernel import controllerservice


class PBEngineClientFactory(pb.PBClientFactory):
    
    def __init__(self, service):
        
        pb.PBClientFactory.__init__(self)
        self.service = service
        self.engineReference = IPBEngine(service)
        self.deferred = self.getRootObject()
        self.deferred.addCallbacks(self._gotRoot, self._getRootFailure)
    
    def _getRootFailure(self, reason):
        """errback for pb.PBClientFactory.getRootObject"""
        reason.raiseException()
    
    def _gotRoot(self, obj):
        """callback for pb.PBClientFactory.getRootObject"""
        self.rootObject = obj
        d = self.rootObject.callRemote('registerEngine', self.engineReference, None)
        d.addCallbacks(self._referenceSent, self._getRootFailure)
        
        return d
    
    def _referenceSent(self, id):
        self.service.id = id
        log.msg("got ID: %r" % id)
        return id
    
    def clientConnectionFailed(self, connector, reason):
        log.msg("connection failed")
    
    def clientConnectionLost(self, connector, reason):
        log.msg("connection lost")
    

# Expose a PB interface to the EngineService
     
class IPBEngine(Interface):
    """Twisted Perspective Broker remote interface for engine service."""
    
    #remote methods for engine service
    def remote_getID(self):
        """return this.id"""
    
    def remote_setID(self, id):
        """set this.id"""
    
    def remote_execute(self, lines):
        """Execute lines of Python code."""
    
    def remote_push(self, namespace):
        """Put value into locals namespace with name key."""
    
    def remote_pull(self, *keys):
        """Gets an item out of the self.locals dict by key."""
    
    def remote_reset(self):
        """Reset the InteractiveShell."""
    
    def remote_kill(self):
        """kill the InteractiveShell."""
    
    def remote_getResult(self, i=None):
        """Get the stdin/stdout/stderr of command i."""
    

class PBEngineReferenceFromService(pb.Referenceable):
    #object necessary for id property
        
    implements(IPBEngine)
    
    def __init__(self, service):
        self.service = service
    
    def remote_getID(self):
        return self.service.id
    
    def remote_setID(self, id):
        self.service.id = id
    
    def remote_execute(self, lines):
        return self.service.execute(lines)
    
    def remote_push(self, pNamespace):
        serialsList = pickle.loads(pNamespace)
        namespace = {}
        for s in serialsList:
            namespace[s.key] = s.unpack()
        return self.service.push(**namespace)
    
    def remote_pull(self, *keys):
        return self.service.pull(*keys)
    
    def remote_reset(self):
        return self.service.reset()

    def remote_kill(self):
        return self.service.kill()
    
    def remote_getResult(self, i=None):
        return self.service.getResult(i)
    

components.registerAdapter(PBEngineReferenceFromService,
                           EngineService,
                           IPBEngine)

#now engine-reference adapter
class EngineFromReference(object):
    
    implements(IEngine)
    
    def __init__(self, reference):
        self.reference = reference
        self._id = None
        self.currentCommand = None
    
    def callRemote(self, *args, **kwargs):
        try:
            return self.reference.callRemote(*args, **kwargs)
        except pb.DeadReferenceError:
            return defer.fail()
    
    def getID(self):
        """return this.id"""
        return self._id
    
    def setID(self, id):
        """set this.id"""
        self._id = id
        return self.callRemote('setID', id)
    
    id = property(getID, setID)
    
    def execute(self, lines):
        """Execute lines of Python code."""
        return self.callRemote('execute', lines)
    
    def push(self, **namespace):
        """Put value into locals namespace with name key."""
        return self.callRemote('push', pickle.dumps(namespace['vanillaNamespace'], 2))
    
    def pull(self, *keys):
        """Gets an item out of the self.locals dict by key."""
        return self.callRemote('pull', *keys)
    
    def reset(self):
        """Reset the InteractiveShell."""
        return self.callRemote('reset')

    def kill(self):
        """Reset the InteractiveShell."""
        return self.callRemote('kill').addErrback(lambda _:defer.succeed(None))
    
    def getResult(self, i=None):
        """Get the stdin/stdout/stderr of command i."""
        return self.callRemote('getResult', i)
    

components.registerAdapter(EngineFromReference,
                        pb.RemoteReference,
                        IEngine)

#for the controller:

class IPBRemoteEngineRoot(Interface):
    """Root object for the controller service Remote Engine server factory"""
    
    def remote_registerEngine(self, engineReference):
        """register new engine on controller"""
    

class PBRemoteEngineRootFromService(pb.Root):
    """Perspective Broker Root object adapter for Controller Service 
    Remote Engine connection"""
    implements(IPBRemoteEngineRoot)
    
    def __init__(self, service):
        self.service = service
    
    def remote_registerEngine(self, engineReference, id):
        engine = IEngine(engineReference)
        remoteEngine = QueuedEngine(engine)
        id = self.service.registerEngine(remoteEngine, id)
        def notify(*args):
            return self.service.disconnectEngine(id)
        
        engineReference.broker.notifyOnDisconnect(notify)
        return id

    

components.registerAdapter(PBRemoteEngineRootFromService,
                        controllerservice.ControllerService,
                        IPBRemoteEngineRoot)


