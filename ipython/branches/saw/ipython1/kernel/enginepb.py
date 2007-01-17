# encoding: utf-8
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
__docformat__ = "restructuredtext en"
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
from twisted.internet import defer, reactor
from twisted.spread import banana
from twisted.internet.interfaces import IProtocolFactory
from zope.interface import Interface, implements, Attribute
from twisted.spread.util import Pager, StringPager, CallbackPageCollector

from twisted.internet.base import DelayedCall
DelayedCall.debug = True

from ipython1.kernel.util import gatherBoth
from ipython1.kernel import newserialized
from ipython1.kernel import controllerservice, protocols
from ipython1.kernel.controllerservice import IControllerBase
from ipython1.kernel.engineservice import \
    IEngineBase, \
    IEngineQueued, \
    EngineService
    
#-------------------------------------------------------------------------------
# This is where you configure the size limit of the banana protocol that
# PB uses.  WARNING, this only works if you are NOT using cBanana, which is
# faster than banana.py.  
#-------------------------------------------------------------------------------
    
#banana.SIZE_LIMIT = 640*1024           # The default of 640 kB
banana.SIZE_LIMIT = 50*1024*1024       # 10 MB
#banana.SIZE_LIMIT = 50*1024*1024       # 50 MB
    
CHUNK_SIZE = 64*1024
    

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
        d = self.rootObject.callRemote('registerEngine', self.engineReference, None)
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

    def remote_pullNamespace(*keys):
        """Pull a namespace of objects by key.
        
        Returns a deferred to a pickled dict of keys, object pairs.
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
    
    def packageFailure(self, f):
        f.cleanFailure()
        pString = pickle.dumps(f, 2)
        return pString
    
    def remote_getID(self):
        return self.service.id
    
    def remote_setID(self, id):
        self.service.id = id
    
    def remote_execute(self, lines):
        return self.service.execute(lines).addErrback(self.packageFailure)
        
    #---------------------------------------------------------------------------
    # Old version of push
    #---------------------------------------------------------------------------
        
    def remote_push(self, pNamespace):
        try:
            namespace = pickle.loads(pNamespace)
        except:
            return failure.Failure()
        else:
            return self.service.push(**namespace).addErrback(self.packageFailure)
        
    #---------------------------------------------------------------------------
    # Paging version of push
    #---------------------------------------------------------------------------

    # NOTE:  These are not being used right now due to problems with PBs 
    # paging handling  (BG 1/15/07).

    def remote_getCollectorForKey(self, key):
        #log.msg("Creating a collector for key" + key)
        if self.collectors.has_key(key):
            return self.packageFailure(failure.fail(failure.Failure( \
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
        d.addErrback(self.packageFailure)
        self.removeCollector(key)
        return d
        
    #---------------------------------------------------------------------------
    # pull
    #---------------------------------------------------------------------------     
        
    def remote_pull(self, *keys):
        d = self.service.pull(*keys)
        return d.addBoth(pickle.dumps, 2)
    
    # NOTE:  The paging version of pull is not being used right now  (BG 1/15/07).
    
    def remote_pullPaging(self, key, collector):
        d = self.service.pull(key)
        d.addCallback(newserialized.serialize)
        d.addCallbacks(self._startPaging, self.packageFailure, callbackArgs=(collector,))
        return d
        
    def _startPaging(self, serial, collector):
        pager = SerializedPager(collector, serial, chunkSize=CHUNK_SIZE)
    
    #---------------------------------------------------------------------------
    # pullNamespace
    #---------------------------------------------------------------------------
    
    def remote_pullNamespace(self, *keys):
        d = self.service.pullNamespace(*keys)
        return d.addBoth(pickle.dumps, 2)
    
    #---------------------------------------------------------------------------
    # Other methods
    #---------------------------------------------------------------------------
    
    def remote_getResult(self, i=None):
        return self.service.getResult(i).addErrback(self.packageFailure)
    
    def remote_reset(self):
        return self.service.reset().addErrback(self.packageFailure)
    
    def remote_kill(self):
        return self.service.kill().addErrback(self.packageFailure)
    
    def remote_keys(self):
        return self.service.keys().addErrback(self.packageFailure)
    
    #---------------------------------------------------------------------------
    # push/pullSerialized
    #---------------------------------------------------------------------------
    
    def remote_pushSerialized(self, pNamespace):
        namespace = pickle.loads(pNamespace)
        d = self.service.pushSerialized(**namespace)
        return d.addErrback(self.packageFailure)
    
    def remote_pullSerialized(self, *keys):
        d = self.service.pullSerialized(*keys)
        d.addCallback(pickle.dumps, 2)
        d.addErrback(self.packageFailure)
        return d


components.registerAdapter(PBEngineReferenceFromService,
                           IEngineBase,
                           IPBEngine)


#-------------------------------------------------------------------------------
# Now the server (Controller) side of things
#-------------------------------------------------------------------------------

class EngineFromReference(object):
    """Adapt a PBReference to an IEngineBase implementing object.
    
    This is invoked when the controller gets a pb.RemoteReference for the engine
    and the controller needs to adapt it to IEngineBase.
    """
    
    implements(IEngineBase)
    
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
        """Return the Engines id."""
        return self._id
    
    def setID(self, id):
        """Set the Engines id."""
        self._id = id
        return self.callRemote('setID', id)
    
    id = property(getID, setID)
    
    #---------------------------------------------------------------------------
    # Methods from IEngine
    #---------------------------------------------------------------------------

    #---------------------------------------------------------------------------
    # execute
    #---------------------------------------------------------------------------
    
    def execute(self, lines):
        return self.callRemote('execute', lines).addCallback(self.checkReturn)

    #---------------------------------------------------------------------------
    # push
    #---------------------------------------------------------------------------

    def pushOld(self, **namespace):
        try:
            package = pickle.dumps(namespace, 2)
        except:
            return failure.Failure()
        else:
            d = self.callRemote('push', package)
            return d.addCallback(self.checkReturn)
            
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
            return failure.Failure()
        else:
            return self.pushPagingSerialized(key, serial)
    
    def pushPagingSerialized(self, key, serial):
        d = self.callRemote('getCollectorForKey', key)
        d.addCallback(self.checkReturn)
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
        return d.addCallback(pickle.loads)
        
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
    # pullNamespace
    #---------------------------------------------------------------------------
    
    def pullNamespace(self, *keys):
        return self.callRemote('pullNamespace', *keys).addCallback(pickle.loads)

    #---------------------------------------------------------------------------
    # Other methods
    #---------------------------------------------------------------------------
    
    def getResult(self, i=None):
        return self.callRemote('getResult', i).addCallback(self.checkReturn)
    
    def reset(self):
        return self.callRemote('reset').addCallback(self.checkReturn)

    def kill(self):
        #this will raise pb.PBConnectionLost on success
        self.callRemote('kill').addErrback(self.killBack)
        return defer.succeed(None)

    def keys(self):
        return self.callRemote('keys').addCallback(self.checkReturn)
    
    #---------------------------------------------------------------------------
    # push/pullSerialized
    #---------------------------------------------------------------------------
        
    def pushSerializedOld(self, **namespace):
        """Older version of pushSerialize."""
        #log.msg(repr(namespace))
        try:
            package = pickle.dumps(namespace, 2)
        except:
            return failure.Failure()
        else:
            d = self.callRemote('pushSerialized', package)
            return d.addCallback(self.checkReturn)
       
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
        return d.addCallback(pickle.loads)

    pushSerialized = pushSerializedOld
 
    #---------------------------------------------------------------------------
    # Misc
    #---------------------------------------------------------------------------
 
    def killBack(self, f):
        try:
            f.raiseException()
        except pb.PBConnectionLost:
            return
    
    def checkReturn(self, r):
        """See if a returned value is a pickled object."""
        if isinstance(r, str):
            try: 
                result = pickle.loads(r)
            except pickle.PickleError:
                return r
            else:
                return result
        else:
            return r


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
    
    def remote_registerEngine(self, engineReference):
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
    
    def remote_registerEngine(self, engineReference, id, *interfaces):
        # First adapt the engineReference to a basic non-queued engine
        engine = IEngineBase(engineReference)
        # Make it an IQueuedEngine before registration
        remoteEngine = IEngineQueued(engine)
        regDict = self.service.registerEngine(remoteEngine, id)
        # Now setup callback for disconnect and unregistering the engine
        def notify(*args):
            return self.service.unregisterEngine(regDict['id'])        
        engineReference.broker.notifyOnDisconnect(notify)
        
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


