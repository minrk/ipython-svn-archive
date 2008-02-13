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
    ISynchronousMultiEngine
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
    
    * xmlrpc_queue_status
    * xmlrpc_clear_queue
    * xmlrpc_get_ids
    
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
        self._deferredIDCallbacks = {}
    
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
    def xmlrpc_get_pending_deferred(self, request, deferredID, block):
        d = self.smultiengine.get_pending_deferred(deferredID, block)
        try:
            callback = self._deferredIDCallbacks.pop(deferredID)
        except KeyError:
            callback = None
        if callback is not None:
            d.addCallback(callback[0], *callback[1], **callback[2])
        return d
       
    @packageResult
    def xmlrpc_clean_out_deferreds(self, request):
        return self.smultiengine.clean_out_deferreds()
    
    def _addDeferredIDCallback(self, did, callback, *args, **kwargs):
        self._deferredIDCallbacks[did] = (callback, args, kwargs)
        return did
        
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
    
    @packageResult
    def xmlrpc_execute(self, request, lines, targets, block):
        return self.smultiengine.execute(lines, targets=targets, block=block)
    
    @packageResult    
    def xmlrpc_push(self, request, binaryNS, targets, block):
        try:
            namespace = pickle.loads(binaryNS.data)
        except:
            d = defer.fail(failure.Failure())
        else:
            d = self.smultiengine.push(namespace, targets=targets, block=block)
        return d
    
    @packageResult
    def xmlrpc_pull(self, request, keys, targets, block):
        d = self.smultiengine.pull(keys, targets=targets, block=block)
        return d
    
    @packageResult    
    def xmlrpc_push_function(self, request, binaryNS, targets, block):
        try:
            namespace = pickle.loads(binaryNS.data)
        except:
            d = defer.fail(failure.Failure())
        else:
            namespace = uncanDict(namespace)
            d = self.smultiengine.push_function(namespace, targets=targets, block=block)
        return d
    
    def _canMultipleKeys(self, result):
        return [canSequence(r) for r in result]
    
    @packageResult
    def xmlrpc_pull_function(self, request, keys, targets, block):
        def can_functions(r, keys):
            if len(keys)==1 or isinstance(keys, str):
                result = canSequence(r)
            elif len(keys)>1:
                result = [canSequence(s) for s in r]
            return result
        d = self.smultiengine.pull_function(keys, targets=targets, block=block)
        if block:
            d.addCallback(can_functions, keys)
        else:
            d.addCallback(lambda did: self._addDeferredIDCallback(did, can_functions, keys))
        return d
    
    @packageResult    
    def xmlrpc_push_serialized(self, request, binaryNS, targets, block):
        try:
            namespace = pickle.loads(binaryNS.data)
        except:
            d = defer.fail(failure.Failure())
        else:
            d = self.smultiengine.push_serialized(namespace, targets=targets, block=block)
        return d
    
    @packageResult
    def xmlrpc_pull_serialized(self, request, keys, targets, block):
        d = self.smultiengine.pull_serialized(keys, targets=targets, block=block)
        return d
    
    @packageResult
    def xmlrpc_get_result(self, request, i, targets, block):
        if i == 'None':
            i = None
        return self.smultiengine.get_result(i, targets=targets, block=block)
    
    @packageResult
    def xmlrpc_reset(self, request, targets, block):
        return self.smultiengine.reset(targets=targets, block=block)
    
    @packageResult
    def xmlrpc_keys(self, request, targets, block):
        return self.smultiengine.keys(targets=targets, block=block)
    
    @packageResult
    def xmlrpc_kill(self, request, controller, targets, block):
        return self.smultiengine.kill(controller, targets=targets, block=block)
    
    @packageResult
    def xmlrpc_clear_queue(self, request, targets, block):
        return self.smultiengine.clear_queue(targets=targets, block=block)
    
    @packageResult
    def xmlrpc_queue_status(self, request, targets, block):
        return self.smultiengine.queue_status(targets=targets, block=block)
    
    @packageResult
    def xmlrpc_set_properties(self, request, binaryNS, targets, block):
        try:
            ns = pickle.loads(binaryNS.data)
        except:
            d = defer.fail(failure.Failure())
        else:
            d = self.smultiengine.set_properties(ns, targets=targets, block=block)
        return d
    
    @packageResult
    def xmlrpc_get_properties(self, request, keys, targets, block):
        if keys=='None':
            keys=None
        return self.smultiengine.get_properties(keys, targets=targets, block=block)
    
    @packageResult
    def xmlrpc_has_properties(self, request, keys, targets, block):
        return self.smultiengine.has_properties(keys, targets=targets, block=block)
    
    @packageResult
    def xmlrpc_del_properties(self, request, keys, targets, block):
        return self.smultiengine.del_properties(keys, targets=targets, block=block)
    
    @packageResult
    def xmlrpc_clear_properties(self, request, targets, block):
        return self.smultiengine.clear_properties(targets=targets, block=block)
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_get_ids(self, request):
        """Get the ids of the registered engines.
        
        This method always blocks.
        """
        return self.smultiengine.get_ids()


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


class XMLRPCSynchronousMultiEngineClient(object):
    
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
        self._deferredIDCallbacks = {}
    
    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------
                 
    def unpackage(self, r):
        return pickle.loads(r.data)
    
    #---------------------------------------------------------------------------
    # Things related to PendingDeferredManager
    #---------------------------------------------------------------------------
    
    def get_pending_deferred(self, deferredID, block=True):
        d = self._proxy.callRemote('get_pending_deferred', deferredID, block)
        d.addCallback(self.unpackage)
        try:
            callback = self._deferredIDCallbacks.pop(deferredID)
        except KeyError:
            callback = None
        if callback is not None:
            d.addCallback(callback[0], *callback[1], **callback[2])
        return d
    
    def clean_out_deferreds(self):
        d = self._proxy.callRemote('clean_out_deferreds', deferredID, block)
        d.addCallback(self.unpackage)
        return d       
    
    def _addDeferredIDCallback(self, did, callback, *args, **kwargs):
        self._deferredIDCallbacks[did] = (callback, args, kwargs)
        return did
       
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
        
    def execute(self, lines, targets='all', block=True):
        d = self._proxy.callRemote('execute', lines, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def push(self, namespace, targets='all', block=True):
        binPackage = xmlrpc.Binary(pickle.dumps(namespace, 2))
        d =  self._proxy.callRemote('push', binPackage, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def pull(self, keys, targets='all', block=True):
        d = self._proxy.callRemote('pull', keys, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def push_function(self, namespace, targets='all', block=True):
        cannedNamespace = canDict(namespace)
        binPackage = xmlrpc.Binary(pickle.dumps(cannedNamespace, 2))
        d = self._proxy.callRemote('push_function', binPackage, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def pull_function(self, keys, targets='all', block=True):
        def uncan_functions(r, keys):
            if len(keys)==1 or isinstance(keys, str):
                return uncanSequence(r)
            elif len(keys)>1:
                return [uncanSequence(s) for s in r]
        d = self._proxy.callRemote('pull_function', keys, targets, block)
        if block:
            d.addCallback(self.unpackage)
            d.addCallback(uncan_functions, keys)
        else:
            d.addCallback(self.unpackage)
            d.addCallback(lambda did: self._addDeferredIDCallback(did, uncan_functions, keys))
        return d
    
    def push_serialized(self, namespace, targets='all', block=True):
        binPackage = xmlrpc.Binary(pickle.dumps(namespace, 2))
        d =  self._proxy.callRemote('push_serialized', binPackage, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def pull_serialized(self, keys, targets='all', block=True):
        d = self._proxy.callRemote('pull_serialized', keys, targets, block)
        d.addCallback(self.unpackage)
        return d
        
    def get_result(self, i=None, targets='all', block=True):
        if i is None: # This is because None cannot be marshalled by xml-rpc
            i = 'None'
        d = self._proxy.callRemote('get_result', i, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def reset(self, targets='all', block=True):
        d = self._proxy.callRemote('reset', targets, block)
        d.addCallback(self.unpackage)
        return d        
    
    def keys(self, targets='all', block=True):
        d = self._proxy.callRemote('keys', targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def kill(self, controller=False, targets='all', block=True):
        d = self._proxy.callRemote('kill', controller, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def clear_queue(self, targets='all', block=True):
        d = self._proxy.callRemote('clear_queue', targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def queue_status(self, targets='all', block=True):
        d = self._proxy.callRemote('queue_status', targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def set_properties(self, properties, targets='all', block=True):
        binPackage = xmlrpc.Binary(pickle.dumps(properties, 2))
        d = self._proxy.callRemote('set_properties', binPackage, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def get_properties(self, keys=None, targets='all', block=True):
        if keys==None:
            keys='None'
        d = self._proxy.callRemote('get_properties', keys, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def has_properties(self, keys, targets='all', block=True):
        d = self._proxy.callRemote('has_properties', keys, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def del_properties(self, keys, targets='all', block=True):
        d = self._proxy.callRemote('del_properties', keys, targets, block)
        d.addCallback(self.unpackage)
        return d
    
    def clear_properties(self, targets='all', block=True):
        d = self._proxy.callRemote('clear_properties', targets, block)
        d.addCallback(self.unpackage)
        return d
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def get_ids(self):
        d = self._proxy.callRemote('get_ids')
        return d

