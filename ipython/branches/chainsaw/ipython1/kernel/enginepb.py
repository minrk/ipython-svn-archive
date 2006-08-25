# -*- test-case-name: ipython1.test.test_enginepb -*-
"""Expose the IPython Kernel Service using Twisted's Perspective Broker.

This module specifies the IPBEngineFromService Interface and its implementation
as an Adapter from the IEngineService Interface.  This adapter wraps
EngineService instance into something that inherits from pb.Referenceable.  This makes
is callable using Perspective Broker.

Any public methods of the IKernelService Interface that should be available over
PB must be added to both the Interface and Adapter in this file.

TODO:

- Make sure the classes fully implement the right interfaces
- Make sure that the methods take the right args and return the right thing
- The right thing here is the correct result or a errback triggered.
"""

#*****************************************************************************
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import cPickle as pickle

from twisted.python import components, log
from twisted.spread import pb
from twisted.internet import defer
from zope.interface import Interface, implements

from ipython1.kernel.engineservice import *
from ipython1.kernel import controllerservice


class PBEngineClientFactory(pb.PBClientFactory):
    """The Client factory on the engine that connects to the controller"""
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
        return d.addCallbacks(self._referenceSent, self._getRootFailure)
    
    def _referenceSent(self, id):
        self.service.id = id
        log.msg("got ID: %r" % id)
        return id
    

# Expose a PB interface to the EngineService
     
class IPBEngine(Interface):
    """Twisted Perspective Broker remote interface for engine service.
    This is NOT the IEngine interface, it is the counterpart to EngineFromReference,
    which does implement IEngine"""
    
    #remote methods for engine service
    def remote_getID():
        """return this.id"""
    
    def remote_setID(id):
        """set this.id"""
    
    def remote_execute(lines):
        """Execute lines of Python code."""
    
    def remote_pushSerialized(namespace):
        """Put value into locals namespace with name key."""
    
    def remote_pull(*keys):
        """"""
    
    def remote_pullSerialized(*keys):
        """Gets an item out of the .locals dict by key."""
    
    def remote_pullNamespace(*keys):
        """Gets a namespace dict from keys"""
    def remote_reset():
        """Reset the InteractiveShell."""
    
    def remote_kill():
        """kill the InteractiveShell."""
    
    def remote_getResult(i=None):
        """Get the stdin/stdout/stderr of command i."""
    
    def remote_status():
        """get status from remote engine"""

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
        namespace = pickle.loads(pNamespace)
        return self.service.push(**namespace)
    
    def remote_pushSerialized(self, pNamespace):
        namespace = pickle.loads(pNamespace)
        return self.service.pushSerialized(**namespace)
    
    def remote_pullSerialized(self, *keys):
        d = self.service.pullSerialized(*keys)
        d.addCallback(pickle.dumps, 2)
        return d
    
    def remote_pull(self, *keys):
        d = self.service.pull(*keys)
        d.addCallback(pickle.dumps, 2)
        return d
    
    def remote_pullNamespace(self, *keys):
        d = self.service.pullNamespace(*keys)
        return d.addCallback(pickle.dumps, 2)
    
    def remote_reset(self):
        return self.service.reset()

    def remote_kill(self):
        return self.service.kill()
    
    def remote_getResult(self, i=None):
        #this is weird
        d = self.service.getResult(i).addCallback(pickle.dumps, 2)
        return d
    
    def remote_status(self):
        # return None
        d = self.service.status()
        return d.addCallback(pickle.dumps, 2)

components.registerAdapter(PBEngineReferenceFromService,
                           EngineService,
                           IPBEngine)

#now engine-reference adapter
class EngineFromReference(object):
    
    implements(IEngineBase, IEngineSerialized)
    
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
    
    def pushSerialized(self, **namespace):
        """Put value into locals namespace with name key."""
        return self.callRemote('pushSerialized', pickle.dumps(namespace, 2))
    
    def push(self, **namespace):
        d = self.callRemote('push', pickle.dumps(namespace, 2))
        return d
    
    def pullSerialized(self, *keys):
        """Gets an item out of the self.locals dict by key."""
        d = self.callRemote('pullSerialized', *keys).addCallback(pickle.loads)
        return d
    
    def pull(self, *keys):
        """Gets an item out of the self.locals dict by key."""
        d = self.callRemote('pull', *keys).addCallback(pickle.loads)
        return d
    
    def pullNamespace(self, *keys):
        """Gets an item out of the self.locals dict by key."""
        return self.callRemote('pullNamespace', *keys).addCallback(pickle.loads)
    
    def reset(self):
        """Reset the InteractiveShell."""
        return self.callRemote('reset')

    def kill(self):
        """Reset the InteractiveShell."""
        #this will raise on success
        return self.callRemote('kill').addErrback(lambda _:defer.succeed(None))
    
    def getResult(self, i=None):
        """Get the stdin/stdout/stderr of command i."""
        return self.callRemote('getResult', i).addCallback(pickle.loads)
    
    def status(self):
        """get the status of the engine"""
        return self.callRemote('status').addCallback(pickle.loads)
    

components.registerAdapter(EngineFromReference,
                        pb.RemoteReference,
                        IEngineBase)

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
    
    def remote_registerEngine(self, engineReference, id, *interfaces):
        engine = IEngineBase(engineReference)
        remoteEngine = completeEngine(QueuedEngine(engine, keepUpToDate=True))
        id = self.service.registerEngine(remoteEngine, id)
        def notify(*args):
            return self.service.unregisterEngine(id)
        
        engineReference.broker.notifyOnDisconnect(notify)
        return id

    

components.registerAdapter(PBRemoteEngineRootFromService,
                        controllerservice.ControllerService,
                        IPBRemoteEngineRoot)


