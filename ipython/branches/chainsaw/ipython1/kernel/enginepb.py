# -*- test-case-name: ipython1.test.test_enginepb -*-
"""Expose the IPython EngineService using Twisted's Perspective Broker.

This modules defines interfaces and adapters to connect an EngineService to
a ControllerService using Perspective Broker.  It defines the following classes:

On the Engine (client) side:

 * IPBEngineClientFactory
 * PBEngineClientFactory
 * IPBEngine
 * PBEngineReferenceFromService
 
On the Controller (server) side:
 
 * EngineFromReference
 * IPBRemoteEngineRoot
 * PBRemoteEngineRootFromService
 * IPBEngineServerFactory
"""

#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import cPickle as pickle

from twisted.python import components, log
from twisted.python.failure import Failure
from twisted.spread import pb
from twisted.internet import defer
from twisted.spread import banana
from zope.interface import Interface, implements

from ipython1.kernel.engineservice import *
from ipython1.kernel import controllerservice, protocols

#-------------------------------------------------------------------------------
# The client (Engine) side of things
#-------------------------------------------------------------------------------

class IPBEngineClientFactory(Interface):
    pass

class PBEngineClientFactory(pb.PBClientFactory, object):
    """PBClientFactory on the Engine that connects to the Controller."""
    
    _MAX_LENGTH = 99999999
    
    def _getSize(self):
        return self._MAX_LENGTH
    
    def _setSize(self, n):
        banana.SIZE_LIMIT = n
        self.engineReference.MAX_LENGTH = n
        self._MAX_LENGTH = n
    
    MAX_LENGTH = property(_getSize, _setSize)
    
    def __init__(self, service):
        
        pb.PBClientFactory.__init__(self)
        self.service = service
        self.engineReference = IPBEngine(service)
        self.engineReference.MAX_LENGTH = self.MAX_LENGTH
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

components.registerAdapter(PBEngineClientFactory, 
                    EngineService, IPBEngineClientFactory)

# Expose a PB interface to the EngineService
     
class IPBEngine(Interface):
    """An interface that exposes an EngineService over PB.
    
    The methods in this interface are similar to those from IEngine, 
    but their arguments and return values are pickled if they are not already
    a string so they can be send over PB.
    """
    
    def remote_getID():
        """return this.id"""
    
    def remote_setID(id):
        """set this.id"""
    
    def remote_execute(lines):
        
    def remote_push(self, pNamespace):
        """Push a namespace into the users namespace.
        
        @arg pNamespace: a pickled namespace.
        """

    def remote_pull(*keys):

    def remote_pullNamespace(*keys):

    def remote_getResult(i=None):
        """Get result i.
        
        Returns a deferred to a pickled result tuple.
        """
        
    def remote_reset():
    
    def remote_kill():
        
    def remote_status():

    def remote_pushSerialized(pNamespace):
        """Push a dict of keys and serialized objects into users namespace.
        
        @arg pNamespace: a pickle namespace of keys and serialized objects.
        """

    def remote_pullSerialized(*keys):
        """Pull objects from users namespace by key as Serialized.
        
        Returns a deferred to a pickled namespace.
        """
    

class PBEngineReferenceFromService(pb.Referenceable, object):
    """Adapt and EngineService to an IPBEngine implementer."""
        
    implements(IPBEngine)
    
    MAX_LENGTH = 99999999
    
    def __init__(self, service):
        self.service = service
    
    def remote_getID(self):
        return self.service.id
    
    def remote_setID(self, id):
        self.service.id = id
    
    def remote_execute(self, lines):
        return self.service.execute(lines).addErrback(pickle.dumps, 2)
    
    def remote_push(self, pNamespace):
        namespace = pickle.loads(pNamespace)
        return self.service.push(**namespace).addErrback(pickle.dumps, 2)
        
    def remote_pull(self, *keys):
        d = self.service.pull(*keys)
        return d.addBoth(pickle.dumps, 2).addCallback(self.checkSize)
    
    def remote_pullNamespace(self, *keys):
        d = self.service.pullNamespace(*keys)
        return d.addBoth(pickle.dumps, 2).addCallback(self.checkSize)
    
    def remote_getResult(self, i=None):
        d = self.service.getResult(i).addBoth(pickle.dumps, 2)
        return d.addCallback(self.checkSize)
    
    def remote_reset(self):
        return self.service.reset().addErrback(pickle.dumps, 2)
    
    def remote_kill(self):
        return self.service.kill().addErrback(pickle.dumps, 2)
    
    def remote_status(self):
        d = self.service.status().addBoth(pickle.dumps, 2)
        return d.addCallback(self.checkSize)
    
    def remote_pushSerialized(self, pNamespace):
        namespace = pickle.loads(pNamespace)
        d = self.service.pushSerialized(**namespace)
        return d.addErrback(pickle.dumps, 2)
    
    def remote_pullSerialized(self, *keys):
        d = self.service.pullSerialized(*keys)
        return d.addBoth(pickle.dumps, 2).addCallback(self.checkSize)
    
    def checkSize(self, package):
        if len(package) > self.MAX_LENGTH:
            package = pickle.dumps(Failure(protocols.MessageSizeError()),2)
        return package


components.registerAdapter(PBEngineReferenceFromService,
                           EngineService,
                           IPBEngine)

#-------------------------------------------------------------------------------
# Now the server (Controller) side of things
#-------------------------------------------------------------------------------

class EngineFromReference(object):
    """Adapt a PBReference to an IEngine implementing object."""
    
    implements(IEngineBase, IEngineSerialized)
    
    MAX_LENGTH = 99999999
    
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
    
    #---------------------------------------------------------------------------
    # Methods from IEngine
    #---------------------------------------------------------------------------
    
    def execute(self, lines):
        if not self.checkSize(lines):
            return defer.fail(Failure(protocols.MessageSizeError()))
        return self.callRemote('execute', lines).addCallback(self.checkReturn)

    def push(self, **namespace):
        package = pickle.dumps(namespace, 2)
        if not self.checkSize(package):
            return defer.fail(Failure(protocols.MessageSizeError()))
        d = self.callRemote('push', package)
        return d.addCallback(self.checkReturn)
    
    def pull(self, *keys):
        d = self.callRemote('pull', *keys)
        return d.addCallback(pickle.loads)
    
    def pullNamespace(self, *keys):
        return self.callRemote('pullNamespace', *keys).addCallback(pickle.loads)

    def getResult(self, i=None):
        return self.callRemote('getResult', i).addCallback(self.checkReturn)
    
    def reset(self):
        return self.callRemote('reset').addCallback(self.checkReturn)

    def kill(self):
        #this will raise pb.PBConnectionLost on success
        self.callRemote('kill').addErrback(self.killBack)
        return defer.succeed(None)

    def status(self):
        return self.callRemote('status').addCallback(self.checkReturn)
    
    def pushSerialized(self, **namespace):
        package = pickle.dumps(namespace, 2)
        if not self.checkSize(package):
            return defer.fail(Failure(protocols.MessageSizeError()))
        d = self.callRemote('pushSerialized', package)
        return d.addCallback(self.checkReturn)
        
    def pullSerialized(self, *keys):
        d = self.callRemote('pullSerialized', *keys)
        return d.addCallback(pickle.loads)
 
    def killBack(self, f):
        try:
            f.raiseException()
        except pb.PBConnectionLost:
            return
    
    def checkReturn(self, r):
        if isinstance(r, str):
            try: 
                return pickle.loads(r)
            except pickle.PickleError:
                pass
        return r
    
    def checkSize(self, package):
        if len(package) < self.MAX_LENGTH:
            return True
    
components.registerAdapter(EngineFromReference,
                        pb.RemoteReference,
                        IEngineBase)

class IPBRemoteEngineRoot(Interface):
    """Interface that tells how an Engine sees a Controller.
    
    Should probably be named IPBRemoteControllerRoot.
    """
    
    def remote_registerEngine(self, engineReference):
        """Register new engine on controller."""
    

class PBRemoteEngineRootFromService(pb.Root):
    """Adapts a ControllerService to an IPBRemoteEngineRoot.
    
    This wraps the ControllerService into something that PB will expose to the 
    EngineService.
    
    Should probably be named PBRemoteControllerRootFromService.
    """
    
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

    
class IPBEngineServerFactory(Interface):
    pass

def PBEngineServerFactoryFromService(service):
    """Adapt a ControllerService to a IPBEngineServerFactory.
    
    Why is this a function rather than a class?
    """
    
    return pb.PBServerFactory(IPBRemoteEngineRoot(service))

components.registerAdapter(PBEngineServerFactoryFromService,
                        controllerservice.ControllerService,
                        IPBEngineServerFactory)


