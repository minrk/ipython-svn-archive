# encoding: utf-8
# -*- test-case-name: ipython1.kernel.test.test_multienginexmlrpc -*-
"""An XML-RPC interface for an `ISynchronousMultiEngine`.

This class lets XML-RPC clients talk to a `ControllerService` through the
`ISynchronousMultiEngine` interface.  The main things this class needs to do
is serialize/unserialize Python objects (using pickle) to be sent as XML-RPC
binary entities.
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

import cPickle as pickle

from zope.interface import Interface, implements
from twisted.internet import defer
from twisted.python import components, failure, log
from twisted.web import xmlrpc as webxmlrpc
from ipython1.external.twisted.web2 import xmlrpc, server, channel

from ipython1.kernel import error 
from ipython1.kernel.util import printer
from ipython1.kernel.multiengine import \
    MultiEngine, \
    IMultiEngine, \
    ISynchronousMultiEngine, \
    SynchronousEngineMultiplexerAll
from ipython1.kernel.multiengineclient import wrapResultList
from ipython1.kernel.xmlrpcutil import Transport
from ipython1.kernel.pickleutil import \
    can, \
    canDict, \
    canSequence, \
    uncan, \
    uncanDict, \
    uncanSequence

# Needed to access the true globals from __main__.__dict__ 
import __main__

#-------------------------------------------------------------------------------
# The Controller side of things
#-------------------------------------------------------------------------------


# This sets the timeout that twisted/web2 uses between requests.
BETWEEN_REQUESTS_TIMEOUT = 15*60


def packageResult(wrappedMethod):
    """Decorator for the methods of XMLRPCMultiEngineFromMultiEngine.
    
    This decorator takes methods of XMLRPCMultiEngineFromMultiEngine
    that return deferreds to results/failures and then registers
    callbacks/errbacks that serialize the result/failure to be sent over
    the wire."""
    def wrappedPackageResult(self, *args, **kwargs):
        d = wrappedMethod(self, *args, **kwargs)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d
    return wrappedPackageResult


class IXMLRPCSynchronousMultiEngine(Interface):
    """XML-RPC interface to `ISynchronousMultiEngine`.  
    
    The methods in this interface are similar to those of 
    `ISynchronousMultiEngine`, but their arguments and return values are pickled
    if they are not already simple Python types that can be send over XML-RPC.
    
    See the documentation of `ISynchronousMultiEngine` and `IMultiEngine` for 
    documentation about the methods.
    
    The methods here take one additional argument (request) that is required
    by XML-RPC, but is not used.
    
    Most methods in this interface act like the `ISynchronousMultiEngine`
    versions and can be called in blocking or non-blocking mode.  There are 
    three methods that always block:
    
    * xmlrpc_queueStatus
    * xmlrpc_clearQueue
    * xmlrpc_getIDs
    
    These methods should always return actual results as they don't need to
    touch the actual engines and can be completed instantly.
    """
    pass


class XMLRPCSynchronousMultiEngineFromMultiEngine(xmlrpc.XMLRPC):
    """Adapt `IMultiEngine` -> `ISynchronousMultiEngine` -> `IXMLRPCSynchronousMultiEngine`.
    """
    
    implements(IXMLRPCSynchronousMultiEngine)
    
    addSlash = True
    
    def __init__(self, multiengine):
        xmlrpc.XMLRPC.__init__(self)
        # Adapt the raw multiengine to `ISynchronousMultiEngine` before saving
        # it.  This allow this class to do two adaptation steps.
        log.msg("Adapting: %r"%multiengine)
        self.smultiengine = ISynchronousMultiEngine(multiengine)
    
    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------
    
    def packageFailure(self, f):
        f.cleanFailure()
        return self.packageSuccess(f)
    
    def packageSuccess(self, obj):
        serial = pickle.dumps(obj, 2)
        return xmlrpc.Binary(serial)
    
    #---------------------------------------------------------------------------
    # Things related to PendingDeferredManager
    #---------------------------------------------------------------------------
    
    @packageResult
    def xmlrpc_getPendingDeferred(self, request, deferredID, block):
        return self.smultiengine.getPendingDeferred(deferredID, block)
       
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
    
    @packageResult
    def xmlrpc_execute(self, request, block, targets, lines):     
        return self.smultiengine.execute(block, targets, lines)
    
    @packageResult    
    def xmlrpc_push(self, request, block, targets, binaryNS):
        try:
            namespace = pickle.loads(binaryNS.data)
        except:
            d = defer.fail(failure.Failure())
        else:
            d = self.smultiengine.push(block, targets, **namespace)
        return d
    
    @packageResult
    def xmlrpc_pull(self, request, block, targets, *keys):
        d = self.smultiengine.pull(block, targets, *keys)
        return d
    
    @packageResult    
    def xmlrpc_pushFunction(self, request, block, targets, binaryNS):
        try:
            namespace = pickle.loads(binaryNS.data)
        except:
            d = defer.fail(failure.Failure())
        else:
            namespace = uncanDict(namespace)
            d = self.smultiengine.pushFunction(block, targets, **namespace)
        return d
    
    def _canMultipleKeys(self, result):
        return [canSequence(r) for r in result]
    
    @packageResult
    def xmlrpc_pullFunction(self, request, block, targets, *keys):
        d = self.smultiengine.pullFunction(block, targets, *keys)
        if len(keys)==1:
            d.addCallback(canSequence)
        elif len(keys)>1:
            d.addCallback(self._canMultipleKeys)
        return d
    
    @packageResult    
    def xmlrpc_pushSerialized(self, request, block, targets, binaryNS):
        try:
            namespace = pickle.loads(binaryNS.data)
        except:
            d = defer.fail(failure.Failure())
        else:
            d = self.smultiengine.pushSerialized(block, targets, **namespace)
        return d
    
    @packageResult
    def xmlrpc_pullSerialized(self, request, block, targets, *keys):
        d = self.smultiengine.pullSerialized(block, targets, *keys)
        return d
    
    @packageResult
    def xmlrpc_getResult(self, request, block, targets, i=None):
        if i == 'None':
            i = None
        return self.smultiengine.getResult(block, targets, i)
    
    @packageResult
    def xmlrpc_reset(self, request, block, targets):
        return self.smultiengine.reset(block, targets)
    
    @packageResult
    def xmlrpc_keys(self, request, block, targets):
        return self.smultiengine.keys(block, targets)
    
    @packageResult
    def xmlrpc_kill(self, request, block, targets, controller=False):
        return self.smultiengine.kill(block, targets, controller)
    
    @packageResult
    def xmlrpc_clearQueue(self, request, block, targets):
        return self.smultiengine.clearQueue(block, targets)
    
    @packageResult
    def xmlrpc_queueStatus(self, request, block, targets):
        return self.smultiengine.queueStatus(block, targets)
    
    @packageResult
    def xmlrpc_setProperties(self, request, block, targets, binaryNS):
        try:
            ns = pickle.loads(binaryNS.data)
        except:
            d = defer.fail(failure.Failure())
        else:
            d = self.smultiengine.setProperties(block, targets, **ns)
        return d
    
    @packageResult
    def xmlrpc_getProperties(self, request, block, targets, *keys):
        return self.smultiengine.getProperties(block, targets, *keys)
    
    @packageResult
    def xmlrpc_hasProperties(self, request, block, targets, *keys):
        return self.smultiengine.hasProperties(block, targets, *keys)
    
    @packageResult
    def xmlrpc_delProperties(self, request, block, targets, *keys):
        return self.smultiengine.delProperties(block, targets, *keys)
    
    @packageResult
    def xmlrpc_clearProperties(self, request, block, targets, *keys):
        return self.smultiengine.clearProperties(block, targets, *keys)
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_getIDs(self, block, request):
        """Get the ids of the registered engines.
        
        This method always blocks.
        """
        return self.smultiengine.getIDs(block)


# The __init__ method of `XMLRPCMultiEngineFromMultiEngine` first adapts the
# `IMultiEngine` to `ISynchronousMultiEngine` so this is actually doing a
# two phase adaptation.
components.registerAdapter(XMLRPCSynchronousMultiEngineFromMultiEngine,
            IMultiEngine, IXMLRPCSynchronousMultiEngine)

class IXMLRPCMultiEngineFactory(Interface):
    pass


def XMLRPCServerFactoryFromMultiEngine(multiengine):
    """Adapt a MultiEngine to a XMLRPCServerFactory."""
    s = server.Site(IXMLRPCSynchronousMultiEngine(multiengine))
    cf = channel.HTTPFactory(s, betweenRequestsTimeOut=BETWEEN_REQUESTS_TIMEOUT)
    return cf


# This adaptation does the final step in:
# `IMultiEngine` -> `ISynchronousMultiEngine` ->
# `IXMLRPCMultiEngine` -> `IXMLRPCMultiEngineFactory`
# The first two steps of this are done above in XMLRPCMultiEngineFromMultiEngine
components.registerAdapter(XMLRPCServerFactoryFromMultiEngine,
            IMultiEngine, IXMLRPCMultiEngineFactory)
        

#-------------------------------------------------------------------------------
# The Client side of things
#-------------------------------------------------------------------------------

class IXMLRPCSynchronousMultiEngineClient(Interface):
    pass


class XMLRPCSynchronousMultiEngineClient(SynchronousEngineMultiplexerAll):
    
    implements(ISynchronousMultiEngine, IXMLRPCSynchronousMultiEngineClient)
    
    def __init__(self, addr):
        """Create a client that will connect to addr.
        
        Once created, this class will autoconnect and reconnect to the
        controller as needed.
        
        :Parameters:
            addr : tuple
                The (ip, port) of the IMultiEngine adapted controller.
        """
        self.addr = addr
        self.url = 'http://%s:%s/' % self.addr
        self._proxy = webxmlrpc.Proxy(self.url)
    
    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------
                 
    def unpackage(self, r):
        return pickle.loads(r.data)
    
    #---------------------------------------------------------------------------
    # Things related to PendingDeferredManager
    #---------------------------------------------------------------------------
    
    def getPendingDeferred(self, deferredID, block):
        d = self._proxy.callRemote('getPendingDeferred', deferredID, block)
        d.addCallback(self.unpackage)
        return d
                   
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
        
    def execute(self, block, targets, lines):
        d = self._proxy.callRemote('execute', block, targets, lines)
        d.addCallback(self.unpackage)
        return d
    
    def push(self, block, targets, **namespace):
        binPackage = xmlrpc.Binary(pickle.dumps(namespace, 2))
        d =  self._proxy.callRemote('push', block, targets, binPackage)
        d.addCallback(self.unpackage)
        return d
    
    def pull(self, block, targets, *keys):
        d = self._proxy.callRemote('pull', block, targets, *keys)
        d.addCallback(self.unpackage)
        return d
    
    def pushFunction(self, block, targets, **namespace):
        cannedNamespace = canDict(namespace)
        binPackage = xmlrpc.Binary(pickle.dumps(cannedNamespace, 2))
        d = self._proxy.callRemote('pushFunction', block, targets, binPackage)
        d.addCallback(self.unpackage)
        return d
    
    def pullFunction(self, block, targets, *keys):
        d = self._proxy.callRemote('pullFunction', block, targets, *keys)
        d.addCallback(self.unpackage)
        d.addCallback(uncanSequence)
        return d
    
    def pushSerialized(self, block, targets, **namespace):
        binPackage = xmlrpc.Binary(pickle.dumps(namespace, 2))
        d =  self._proxy.callRemote('pushSerialized', block, targets, binPackage)
        d.addCallback(self.unpackage)
        return d
    
    def pullSerialized(self, block, targets, *keys):
        d = self._proxy.callRemote('pullSerialized', block, targets, *keys)
        d.addCallback(self.unpackage)
        return d
        
    def getResult(self, block, targets, i=None):
        if i is None: # This is because None cannot be marshalled by xml-rpc
            i = 'None'
        d = self._proxy.callRemote('getResult', block, targets, i)
        d.addCallback(self.unpackage)
        return d
    
    def reset(self, block, targets):
        d = self._proxy.callRemote('reset', block, targets)
        d.addCallback(self.unpackage)
        return d        
    
    def keys(self, block, targets):
        d = self._proxy.callRemote('keys', block, targets)
        d.addCallback(self.unpackage)
        return d
    
    def kill(self, block, targets, controller=False):
        d = self._proxy.callRemote('kill', block, targets, controller)
        d.addCallback(self.unpackage)
        return d
    
    def clearQueue(self, block, targets):
        d = self._proxy.callRemote('clearQueue', block, targets)
        d.addCallback(self.unpackage)
        return d
    
    def queueStatus(self, block, targets):
        d = self._proxy.callRemote('queueStatus', block, targets)
        d.addCallback(self.unpackage)
        return d
    
    def setProperties(self, block, targets, **properties):
        binPackage = xmlrpc.Binary(pickle.dumps(properties, 2))
        d = self._proxy.callRemote('setProperties', block, targets, binPackage)
        d.addCallback(self.unpackage)
        return d
    
    def getProperties(self, block, targets, *keys):
        d = self._proxy.callRemote('getProperties', block, targets, *keys)
        d.addCallback(self.unpackage)
        return d
    
    def hasProperties(self, block, targets, *keys):
        d = self._proxy.callRemote('hasProperties', block, targets, *keys)
        d.addCallback(self.unpackage)
        return d
    
    def delProperties(self, block, targets, *keys):
        d = self._proxy.callRemote('delProperties', block, targets, *keys)
        d.addCallback(self.unpackage)
        return d
    
    def clearProperties(self, block, targets):
        d = self._proxy.callRemote('clearProperties', block, targets, *keys)
        d.addCallback(self.unpackage)
        return d
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def getIDs(self, block):
        d = self._proxy.callRemote('getIDs', block)
        return d

