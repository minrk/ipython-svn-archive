# encoding: utf-8
# -*- test-case-name: ipython1.kernel.test.test_enginepb -*-
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
__docformat__ = "restructuredtext en"
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelley <benjaminrk@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import os, time
import cPickle as pickle

from twisted.python import components, log, failure
from twisted.python.failure import Failure
from twisted.spread import pb
from twisted.internet import defer, reactor, threads
from twisted.internet.interfaces import IProtocolFactory
from zope.interface import Interface, implements, Attribute
from twisted.spread.util import Pager, StringPager, CallbackPageCollector

from twisted.internet.base import DelayedCall
DelayedCall.debug = True

from ipython1.kernel import pbconfig
from ipython1.kernel.pbutil import packageFailure, unpackageFailure, checkMessageSize
from ipython1.kernel.pbconfig import CHUNK_SIZE
from ipython1.kernel.util import printer
from ipython1.kernel.twistedutil import gatherBoth
from ipython1.kernel import newserialized
from ipython1.kernel.error import PBMessageSizeError, ProtocolError
from ipython1.kernel import controllerservice
from ipython1.kernel.controllerservice import IControllerBase
from ipython1.kernel.engineservice import \
    IEngineBase, \
    IEngineQueued, \
    EngineService, \
    StrictDict
from ipython1.kernel.pickleutil import \
    can, \
    canDict, \
    canSequence, \
    uncan, \
    uncanDict, \
    uncanSequence
    
    
#-------------------------------------------------------------------------------
# Classes to enable paging of large objects
#-------------------------------------------------------------------------------
  
# NOTE:  The paging versions of push/pull/etc are not being used as there is 
# a problem with the way that deferreds are created but not handled in the 
# internals of pb.brokers (BG 1/15/07).
  
class SerializedPager(StringPager):
    
    def __init__(self, collector, serial, chunkSize=8192, callback=None, *args, **kw):
        
        # Save the pickled metadata to self._firstPage and pass the
        # data to StringPager.__init__
        assert newserialized.ISerialized.providedBy(serial)
        self._atFirstPage = True
        md = serial.getMetadata()
        md['type'] = serial.getTypeDescriptor()
        self._firstPage = pickle.dumps(md, 2)
        data = serial.getData()
        
        StringPager.__init__(self, collector, data, chunkSize, callback, *args, **kw)

    def nextPage(self):
        if self._atFirstPage:
            self._atFirstPage = False
            return self._firstPage
        else:
            return StringPager.nextPage(self)



class DeferredCollector(pb.Referenceable):
    
    def __init__(self):
        self.pages = []
        self._deferred = defer.Deferred()
        
    def remote_gotPage(self, page):
        self.pages.append(page)

    def remote_endedPaging(self):
        #self.pagesReceived()
        # The pagesReceived method triggers the actual object to be returned to the
        # requester.  This callLater is needed to ensure that other Deferreds are
        # first closed up.  This is related to the internal problems in PBs paging
        # machinery  (BG 1/15/07).
        reactor.callLater(0.1, self.pagesReceived)       
        
    def getDeferredToCollected(self):
        return self._deferred
        
    def pagesReceived(self):
        """Do something with self.pages, and call self._deferred.call[err]back."""
        raise NotImplementedError("You must implement handlePages")


class SerializedCollector(DeferredCollector):
    
    def __init__(self):
        DeferredCollector.__init__(self)

    def pagesReceived(self):
        metadataString = self.pages[0]
        dataString = ''.join(self.pages[1:])
        try:
            metadata = pickle.loads(metadataString)
        except:
            self._deferred.errback(failure.Failure())
        else:
            typeDescriptor = metadata.pop('type')
            serial = newserialized.Serialized(dataString, typeDescriptor, metadata)
            self._deferred.callback(serial)

class CollectorCollision(Exception):
    pass
    
    
#-------------------------------------------------------------------------------
# The client (Engine) side of things
#-------------------------------------------------------------------------------

class IPBEngineClientFactory(Interface):
    pass

class PBEngineClientFactory(pb.PBClientFactory, object):
    """PBClientFactory on the Engine that connects to the Controller.
    
    This makes an implementer of IEngineBase (IEngineCore+IEngineSerialized)
    look like a client factory that can be used in connectTCP.
    """
        
    implements(IPBEngineClientFactory)
        
    def __init__(self, service):
        
        assert IEngineBase.providedBy(service), \
            "IEngineBase is not provided by " + repr(service)
        pb.PBClientFactory.__init__(self)
        self.service = service
        self.engineReference = IPBEngine(service)
        self.deferred = self.getRootObject()
        self.deferred.addCallbacks(self._gotRoot, self._getRootFailure)
    
    def _getRootFailure(self, reason):
        """errback for pb.PBClientFactory.getRootObject"""
        log.err(reason)
        #return reason
        
    def _gotRoot(self, obj):
        """callback for pb.PBClientFactory.getRootObject"""
        
        self.rootObject = obj
        # Now register myself with the controller
        desiredID = self.service.id
        d = self.rootObject.callRemote('registerEngine', self.engineReference, 
            desiredID, os.getpid(), pickle.dumps(self.service.properties,2))
        return d.addCallbacks(self._referenceSent, self._getRootFailure)
    
    def _referenceSent(self, registrationDict):
        self.service.id = registrationDict['id']
        log.msg("got ID: %r" % self.service.id)
        return self.service.id


components.registerAdapter(PBEngineClientFactory, 
                    IEngineBase, IPBEngineClientFactory)


# Expose a PB interface to the EngineService
     
class IPBEngine(Interface):
    """An interface that exposes an EngineService over PB.
    
    The methods in this interface are similar to those from IEngine, 
    but their arguments and return values slightly different to reflect
    that PB cannot send arbitrary objects.  We handle this by pickling/
    unpickling that the two endpoints.
    
    If a remote or local exception is raised, the appropriate Failure
    will be returned instead.
    """
        
    def remote_getID():
        """return this.id"""
    
    def remote_setID(id):
        """set this.id"""
    
    def remote_execute(lines):
        """Execute lines of Python code.
        
        Returns a deferred to a result dict.
        
        Upon failure returns a pickled Failure.
        """
    
    def remote_push(self, pNamespace):
        """Push a namespace into the users namespace.
        
        pNamespace is a pickled dict of key, object pairs. 
        """
    
    def remote_pull(*keys):
        """Pull objects from a users namespace by keys.
        
        Returns a deferred to a pickled tuple of objects.  If any single
        key has a problem, the Failure of that will be returned.
        """
    
    def remote_getResult(i=None):
        """Get result i.
        
        Returns a deferred to a pickled result dict.
        """
    
    def remote_reset():
        """Reset the Engine."""
    
    def remote_kill():
        """Stop the Engines reactor."""
    
    def remote_keys():
        """Get variable names that are currently defined in the user's namespace.
        
        Returns a deferred to a tuple of keys.
        """
    
    def remote_pushSerialized(pNamespace):
        """Push a dict of keys and serialized objects into users namespace.
        
        @arg pNamespace: a pickle namespace of keys and serialized objects.
        """
    
    def remote_pullSerialized(*keys):
        """Pull objects from users namespace by key as Serialized.
        
        Returns a deferred to a pickled dict of key, Serialized pairs.
        """
    
    def remote_setProperties(pNamespace):
        """update the properties for this engine"""
    
    def remote_getProperties(*keys):
        """pull a subdict of the properties for this engine by keys"""
    
    def remote_hasProperties(*keys):
        """check for keys in the properties for this engine"""
    
    def remote_delProperties(*keys):
        """remove values of the properties for this engine by keys"""
    
    def remote_clearProperties():
        """clear the properties for this engine"""
    
    


class PBEngineReferenceFromService(pb.Referenceable, object):
    """Adapt an IEngineBase to an IPBEngine implementer exposing it to PB.
    
    This exposes the IEngineBase implementer to a controller, but adapts it
    properly for use with PB.
    """
        
    implements(IPBEngine)
    
    def __init__(self, service):
        # service is an IEngineBase implementer, like EngineService
        assert IEngineBase.providedBy(service), \
            "IEngineBase is not provided by" + repr(service)
        self.service = service
        self.collectors = {}
    
    def remote_getID(self):
        return self.service.id
    
    def remote_setID(self, id):
        self.service.id = id
    
    def _checkProperties(self, result):
        dosync = self.service.properties.modified
        self.service.properties.modified = False
        return (dosync and pickle.dumps(self.service.properties, 2)), result
    
    def remote_execute(self, lines):
        d = self.service.execute(lines)
        d.addErrback(packageFailure)
        d.addCallback(self._checkProperties)
        d.addErrback(packageFailure)
        #d.addCallback(lambda r: log.msg("Got result: " + str(r)))
        return d
    
    def remote_setProperties(self, pNamespace):
        try:
            namespace = pickle.loads(pNamespace)
        except:
            return defer.fail(failure.Failure()).addErrback(packageFailure)
        else:
            return self.service.setProperties(**namespace).addErrback(packageFailure)
    
    def remote_getProperties(self, *keys):
        d = self.service.getProperties(*keys)
        d.addCallback(pickle.dumps, 2)
        d.addCallback(checkMessageSize, repr(keys))
        d.addErrback(packageFailure)
        return d
    
    def remote_hasProperties(self, *keys):
        d = self.service.hasProperties(*keys)
        d.addCallback(pickle.dumps, 2)
        d.addCallback(checkMessageSize, repr(keys))
        d.addErrback(packageFailure)
        return d
    
    def remote_delProperties(self, *keys):
        d = self.service.delProperties(*keys)
        # d.addCallback(pickle.dumps, 2)
        # d.addCallback(checkMessageSize, repr(keys))
        d.addErrback(packageFailure)
        return d
    
    def remote_clearProperties(self):
        d = self.service.clearProperties()
        # d.addCallback(pickle.dumps, 2)
        # d.addCallback(checkMessageSize, repr(keys))
        d.addErrback(packageFailure)
        return d
    
    
    #---------------------------------------------------------------------------
    # Old version of push
    #---------------------------------------------------------------------------
        
    def remote_push(self, pNamespace):
        try:
            namespace = pickle.loads(pNamespace)
        except:
            return defer.fail(failure.Failure()).addErrback(packageFailure)
        else:
            # The usage of globals() here is an attempt to bind any pickled functions
            # to the globals of this module.  What we really want is to have it bound
            # to the globals of the callers module.  This will require walking the 
            # stack.  BG 10/3/07.
            namespace = uncanDict(namespace, globals())
            return self.service.push(**namespace).addErrback(packageFailure)
    
    #---------------------------------------------------------------------------
    # Paging version of push
    #---------------------------------------------------------------------------
    
    # NOTE:  These are not being used right now due to problems with PBs 
    # paging handling  (BG 1/15/07).
    
    def remote_getCollectorForKey(self, key):
        #log.msg("Creating a collector for key" + key)
        if self.collectors.has_key(key):
            return packageFailure(defer.fail(failure.Failure( \
                CollectorCollision("Collector for key %s already exists" % key))))
        coll = SerializedCollector()
        self.collectors[key] = coll
        return coll
    
    def removeCollector(self, key):
        if self.collectors.has_key(key):
            self.collectors.pop(key)
    
    def remote_finishPushPaging(self, key):
        #log.msg("finishPushPaging for key: " + key)
        coll = self.collectors.get(key, None)
        if coll is None:
            return 'no collector for key'
        else:
            d = coll.getDeferredToCollected()
            d.addCallback(self.handlePagedPush, key)
            return d
    
    def handlePagedPush(self, serial, key):
        log.msg("I got a serial! " + repr(serial) + key)
        d = self.service.pushSerialized(**{key:serial})           
        d.addErrback(packageFailure)
        self.removeCollector(key)
        return d
    
    #---------------------------------------------------------------------------
    # pull
    #---------------------------------------------------------------------------     
                
    def remote_pull(self, *keys):
        d = self.service.pull(*keys)
        if len(keys)>1:
            d.addCallback(canSequence)
        elif len(keys)==1:
            d.addCallback(can)
        d.addCallback(pickle.dumps, 2)
        d.addCallback(checkMessageSize, repr(keys))
        d.addErrback(packageFailure)
        return d
    
    # NOTE:  The paging version of pull is not being used right now  (BG 1/15/07).
    
    def remote_pullPaging(self, key, collector):
        d = self.service.pull(key)
        d.addCallback(newserialized.serialize)
        d.addCallbacks(self._startPaging, packageFailure, callbackArgs=(collector,))
        return d
    
    def _startPaging(self, serial, collector):
        pager = SerializedPager(collector, serial, chunkSize=CHUNK_SIZE)
    
    #---------------------------------------------------------------------------
    # Other methods
    #---------------------------------------------------------------------------
    
    def remote_getResult(self, i=None):
        return self.service.getResult(i).addErrback(packageFailure)
    
    def remote_reset(self):
        return self.service.reset().addErrback(packageFailure)
    
    def remote_kill(self):
        return self.service.kill().addErrback(packageFailure)
    
    def remote_keys(self):
        return self.service.keys().addErrback(packageFailure)
    
    #---------------------------------------------------------------------------
    # push/pullSerialized
    #---------------------------------------------------------------------------
    
    def remote_pushSerialized(self, pNamespace):
        try:
            namespace = pickle.loads(pNamespace)
        except:
            return defer.fail(failure.Failure()).addErrback(packageFailure)
        else:
            d = self.service.pushSerialized(**namespace)
            return d.addErrback(packageFailure)
    
    def remote_pullSerialized(self, *keys):
        d = self.service.pullSerialized(*keys)
        d.addCallback(pickle.dumps, 2)
        d.addCallback(checkMessageSize, repr(keys))
        d.addErrback(packageFailure)
        return d
    

components.registerAdapter(PBEngineReferenceFromService,
                           IEngineBase,
                           IPBEngine)


#-------------------------------------------------------------------------------
# Now the server (Controller) side of things
#-------------------------------------------------------------------------------

class FailureUnpickleable(Exception):
    pass

class EngineFromReference(object):
    """Adapt a PBReference to an IEngineBase implementing object.
    
    This is invoked when the controller gets a pb.RemoteReference for the engine
    and the controller needs to adapt it to IEngineBase.
    """
    
    implements(IEngineBase)
    
    def __init__(self, reference):
        self.reference = reference
        self._id = None
        self._properties = StrictDict()
        self.currentCommand = None
    
    def callRemote(self, *args, **kwargs):
        try:
            return self.reference.callRemote(*args, **kwargs)
        except pb.DeadReferenceError:
            self.notifier()
            self.stopNotifying(self.notifier)
            return defer.fail()
    
    def getID(self):
        """Return the Engines id."""
        return self._id
    
    def setID(self, id):
        """Set the Engines id."""
        self._id = id
        return self.callRemote('setID', id)
    
    id = property(getID, setID)
    
    def syncProperties(self, r):
        try:
            psync, result = r
        except (ValueError, TypeError):
            return r
        else:
            if psync:
                log.msg("sync properties")
                pick = self.checkReturnForFailure(psync)
                if isinstance(pick, failure.Failure):
                    self.properties = pick
                    return pick
                else:
                    self.properties = pickle.loads(pick)
            return result
    
    def _setProperties(self, dikt):
        self._properties.clear()
        self._properties.update(dikt)
        # self._properties.update(dikt)
    
    def _getProperties(self):
        if isinstance(self._properties, failure.Failure):
            self._properties.raiseException()
        return self._properties
    
    properties = property(_getProperties, _setProperties)
    
    #---------------------------------------------------------------------------
    # Methods from IEngine
    #---------------------------------------------------------------------------
    
    #---------------------------------------------------------------------------
    # execute
    #---------------------------------------------------------------------------
    
    def execute(self, lines):
        # self._needProperties = True
        d = self.callRemote('execute', lines)
        d.addCallback(self.syncProperties)
        return d.addCallback(self.checkReturnForFailure)
    
    #---------------------------------------------------------------------------
    # push
    #---------------------------------------------------------------------------
    
    def pushOld(self, **namespace):
        try:
            package = pickle.dumps(canDict(namespace), 2)
        except:
            return defer.fail(failure.Failure())
        else:
            package = checkMessageSize(package, namespace.keys())
            if isinstance(package, failure.Failure):
                return defer.fail(package)
            else:
                d = self.callRemote('push', package)
                return d.addCallback(self.checkReturnForFailure)
    
    # Paging version
    
    def pushNew(self, **namespace):
        dList = []
        for k, v in namespace.iteritems():
            d = self.pushPaging(k, v)
            dList.append(d)
        return gatherBoth(dList, 
                          fireOnOneErrback=1,
                          logErrors=0, 
                          consumeErrors=1)
    
    def pushPaging(self, key, obj):
        try:
            serial = newserialized.serialize(obj)
        except:
            return defer.fail(failure.Failure())
        else:
            return self.pushPagingSerialized(key, serial)
    
    def pushPagingSerialized(self, key, serial):
        d = self.callRemote('getCollectorForKey', key)
        d.addCallback(self.checkReturnForFailure)
        d.addCallback(self._beginPaging, serial, key) 
        return d
    
    def _beginPaging(self, collector, serial, key):
        #log.msg("Beginning to page" + repr(collector))
        pager = SerializedPager(collector, serial, chunkSize=CHUNK_SIZE)
        d = self.callRemote('finishPushPaging', key)
        return d
    
    push = pushOld
    
    #---------------------------------------------------------------------------
    # pull
    #---------------------------------------------------------------------------
        
    def pullOld(self, *keys):
        d = self.callRemote('pull', *keys)
        d.addCallback(self.checkReturnForFailure)
        d.addCallback(pickle.loads)
        # The usage of globals() here is an attempt to bind any pickled functions
        # to the globals of this module.  What we really want is to have it bound
        # to the globals of the callers module.  This will require walking the 
        # stack.  BG 10/3/07.
        if len(keys)>1:
            d.addCallback(uncanSequence, globals())
        elif len(keys)>0:
            d.addCallback(uncan, globals())
        return d
    
    # Paging version
        
    def pullPaging(self, key):
        collector = SerializedCollector()
        # This will fire if the object cannot be serialized on the other side
        d = self.callRemote('pullPaging', key, collector)
        d.addCallback(lambda _: collector.getDeferredToCollected())
        d.addCallback(newserialized.unserialize)
        return d
    
    def pullNew(self, *keys):
        if len(keys) == 1:
            return self.pullPaging(keys[0])
        else:
            pulledDeferreds = []
            for k in keys:
                pulledDeferreds.append(self.pullPaging(k))
            d = gatherBoth(pulledDeferreds,
                           fireOnOneErrback=1,
                           logErrors=0, 
                           consumeErrors=1)
            return d
    
    pull = pullOld
    
    #---------------------------------------------------------------------------
    # Other methods
    #---------------------------------------------------------------------------
    
    def getResult(self, i=None):
        return self.callRemote('getResult', i).addCallback(self.checkReturnForFailure)
    
    def reset(self):
        self._refreshProperties = True
        d = self.callRemote('reset')
        d.addCallback(self.syncProperties)
        return d.addCallback(self.checkReturnForFailure)
    
    def kill(self):
        #this will raise pb.PBConnectionLost on success
        d = self.callRemote('kill')
        d.addCallback(self.syncProperties)
        d.addCallback(self.checkReturnForFailure)
        d.addErrback(self.killBack)
        return d
    
    def killBack(self, f):
        f.trap(pb.PBConnectionLost)
        return None
    
    def keys(self):
        return self.callRemote('keys').addCallback(self.checkReturnForFailure)
    
    #---------------------------------------------------------------------------
    # Properties methods
    #---------------------------------------------------------------------------
    
    def setProperties(self, **properties):
        try:
            package = pickle.dumps(properties, 2)
        except:
            return defer.fail(failure.Failure())
        else:
            package = checkMessageSize(package, properties.keys())
            if isinstance(package, failure.Failure):
                return defer.fail(package)
            else:
                d = self.callRemote('setProperties', package)
                return d.addCallback(self.checkReturnForFailure)
        return d
    
    def getProperties(self, *keys):
        d = self.callRemote('getProperties', *keys)
        d.addCallback(self.checkReturnForFailure)
        d.addCallback(pickle.loads)
        return d
    
    def hasProperties(self, *keys):
        d = self.callRemote('hasProperties', *keys)
        d.addCallback(self.checkReturnForFailure)
        d.addCallback(pickle.loads)
        return d
    
    def delProperties(self, *keys):
        d = self.callRemote('delProperties', *keys)
        d.addCallback(self.checkReturnForFailure)
        # d.addCallback(pickle.loads)
        return d
    
    def clearProperties(self):
        d = self.callRemote('clearProperties')
        d.addCallback(self.checkReturnForFailure)
        return d
    
    
    
    #---------------------------------------------------------------------------
    # push/pullSerialized
    #---------------------------------------------------------------------------
        
    def pushSerializedOld(self, **namespace):
        """Older version of pushSerialize."""
        #log.msg(repr(namespace))
        try:
            package = pickle.dumps(namespace, 2)
        except:
            return defer.fail(failure.Failure())
        else:
            package = checkMessageSize(package, namespace.keys())
            if isinstance(package, failure.Failure):
                return defer.fail(package)
            else:
                d = self.callRemote('pushSerialized', package)
                return d.addCallback(self.checkReturnForFailure)
    
    # The new paging version
    
    def pushSerializedNew(self, **namespace):      
        dList = []
        for k, v in namespace.iteritems():
            d = self.pushPagingSerialized(k, v)
            dList.append(d)
        return gatherBoth(dList,
                          fireOnOneErrback=1,
                          logErrors=0, 
                          consumeErrors=1)
    
    def pullSerialized(self, *keys):
        d = self.callRemote('pullSerialized', *keys)
        d.addCallback(self.checkReturnForFailure)
        d.addCallback(pickle.loads)
        return d
    
    pushSerialized = pushSerializedOld
 
    #---------------------------------------------------------------------------
    # Misc
    #---------------------------------------------------------------------------
     
    def checkReturnForFailure(self, r):
        """See if a returned value is a pickled Failure object.
        
        To distinguish between general pickled objects and pickled Failures, the
        other side should prepend the string FAILURE: to any pickled Failure.
        """
        return unpackageFailure(r)
    

components.registerAdapter(EngineFromReference,
    pb.RemoteReference,
    IEngineBase)


#-------------------------------------------------------------------------------
# Now adapt an IControllerBase to incoming PB connections
#-------------------------------------------------------------------------------


class IPBRemoteEngineRoot(Interface):
    """Interface that tells how an Engine sees a Controller.
    
    This interface basically exposes the actual ControllerService
    to PB.
    """
    
    def remote_registerEngine(self, engineReference, id=None, pid=None, pproperties=None):
        """Register new engine on controller."""
    

class PBRemoteEngineRootFromService(pb.Root):
    """Adapts a IControllerBase to an IPBRemoteEngineRoot.
    
    This is an adapter between the actual ControllerService that
    implements IControllerBase and PB.
    """
    
    implements(IPBRemoteEngineRoot)
    
    def __init__(self, service):
        assert IControllerBase.providedBy(service), \
            "IControllerBase is not provided by " + repr(service)
        self.service = service
    
    def remote_registerEngine(self, engineReference, id=None, pid=None, pproperties=None):
        # First adapt the engineReference to a basic non-queued engine
        engine = IEngineBase(engineReference)
        if pproperties:
            engine.properties = pickle.loads(pproperties)
        # Make it an IQueuedEngine before registration
        remoteEngine = IEngineQueued(engine)
        # Get the ip/port of the remote side
        peerAddress = engineReference.broker.transport.getPeer()
        ip = peerAddress.host
        port = peerAddress.port
        regDict = self.service.registerEngine(remoteEngine, id, ip, port, pid)
        # Now setup callback for disconnect and unregistering the engine
        def notify(*args):
            return self.service.unregisterEngine(regDict['id'])        
        engineReference.broker.notifyOnDisconnect(notify)
        
        engine.notifier = notify
        engine.stopNotifying = engineReference.broker.dontNotifyOnDisconnect
        
        return regDict


components.registerAdapter(PBRemoteEngineRootFromService,
                        IControllerBase,
                        IPBRemoteEngineRoot)


#-------------------------------------------------------------------------------
# Now the Server Factory for PB connections
#-------------------------------------------------------------------------------

class IPBEngineServerFactory(IProtocolFactory):
    """This is the server factory used by PB on the controller."""
    pass


class PBEngineServerFactory(pb.PBServerFactory):
    
    implements(IPBEngineServerFactory)
    
    
def PBEngineServerFactoryFromService(service):
    """Adapt a IControllerBase to a IPBEngineServerFactory.
    
    :Parameters:
     - `service`: A IControllerBase implementing service.
     
    This adapter is not a class because it returns a PBEngineServerFactory
    that already has the PB root passed to it.  It is really doing
    double adaptation so it is a little unusual:
    
    service -> PB root
    service -> PBEngineServerFactory
    """
    assert IControllerBase.providedBy(service), \
        "IControllerBase is not provided by " + repr(service)
    root = IPBRemoteEngineRoot(service)
    return PBEngineServerFactory(root)


components.registerAdapter(PBEngineServerFactoryFromService,
                        IControllerBase,
                        IPBEngineServerFactory)


