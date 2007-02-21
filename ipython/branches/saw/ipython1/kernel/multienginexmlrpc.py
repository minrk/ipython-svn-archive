# encoding: utf-8
# -*- test-case-name: ipython1.test.test_multienginexmlrpc -*-
"""An XML-RPC interface to a MultiEngine.

This class lets XMLRPC clients talk to the ControllerService.  The main difficulty
is that XMLRPC doesn't allow arbitrary objects to be sent over the wire - only
basic Python types.  To get around this we simple pickle more complex objects
on boths side of the wire.  That is the main thing these classes have to 
manage.
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
import xmlrpclib

from zope.interface import Interface, implements
from twisted.internet import defer
from twisted.python import components, failure

from ipython1.external.twisted.web2 import xmlrpc, server, channel

from ipython1.kernel import error, blockon
from ipython1.kernel.multiengine import MultiEngine, IMultiEngine
from ipython1.kernel.multiengine import ISynchronousMultiEngine
from ipython1.kernel.multiengineclient import ConnectingMultiEngineClient

#-------------------------------------------------------------------------------
# The Controller side of things
#-------------------------------------------------------------------------------

class IXMLRPCMultiEngine(Interface):
    """XML-RPC interface to controller.  

    The methods in this interface are similar to those from IEngineMultiplexer, 
    but their arguments and return values are pickled if they are not already
    simple Python types so they can be send over XMLRPC.  This is to deal with 
    the fact that w/o a lot of work XMLRPC cannot send arbitrary objects over the
    wire.

    See the documentation of IEngineMultiplexer for documentation about the methods.
    """
            
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
            
    def xmlrpc_execute(request, clientID, block, targets, lines):
        """"""
        
    def xmlrpc_push(request, clientID, block, targets, namespace):
        """"""
        
    def xmlrpc_pull(request, clientID, block, targets, *keys):
        """"""
        
    def xmlrpc_getResult(request, clientID, block, targets, i=None):
        """"""
        
    def xmlrpc_reset(request, clientID, block, targets):
        """"""
        
    def xmlrpc_keys(request, clientID, block, targets):
        """"""
        
    def xmlrpc_kill(request, clientID, block, targets, controller=False):
        """"""
        
    def xmlrpc_pushSerialized(request, clientID, block, targets, namespace):
        """"""
        
    def xmlrpc_pullSerialized(request, clientID, block, targets, *keys):
        """"""
        
    def xmlrpc_clearQueue(request, clientID, targets):
        """Always block!"""
        
    def xmlrpc_queueStatus(request, clientID, targets):
        """Always block!"""
        
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
        
    def xmlrpc_getIDs(request):
        """Always block"""
        
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
        
    def xmlrpc_scatter(request, clientID, block, targets, key, seq, style='basic', flatten=False):
        """"""
        
    def xmlrpc_gather(request, clientID, block, targets, key, style='basic'):
        """"""
    #---------------------------------------------------------------------------
    # Pending Deferred related methods
    #---------------------------------------------------------------------------            
    
    def xmlrpc_registerClient(request):
        """"""
        
    def xmlrpc_unregisterClient(request, clientID):
        """"""

    def xmlrpc_getPendingResult(request, clientID, resultID):
        """"""
        
    def xmlrpc_getAllPendingDeferreds(self, clientID):
        """"""
        
class XMLRPCMultiEngineFromMultiEngine(xmlrpc.XMLRPC):
    """XML-RPC attachmeot for controller.
    
    See IXMLRPCMultiEngine and IMultiEngine (and its children) for documentation. 
    """
    implements(IXMLRPCMultiEngine)
    
    addSlash = True
    
    def __init__(self, multiengine):
        xmlrpc.XMLRPC.__init__(self)
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
    # IXMLRPCTaskController related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_getClientID(self, request):
        clientID = self.clientIndex
        self.clientIndex += 1
        return clientID
    
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_execute(self, request, clientID, block, targets, lines):
        if not self.smultiengine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:        
            d = self.smultiengine.execute(clientID, block, targets, lines)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d
    
    def xmlrpc_push(self, request, clientID, block, targets, binaryNS):
        if not self.smultiengine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            try:
                namespace = pickle.loads(binaryNS.data)
            except:
                d = defer.fail(failure.Failure())
            else:
                d = self.smultiengine.push(targets, clientID, block, **namespace)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d
    
    def xmlrpc_pull(self, request, clientID, block, targets, *keys):
        if not self.smultiengine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.smultiengine.pull(targets, clientID, block, *keys)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d
    
    def xmlrpc_getResult(self, request, clientID, block, targets, i=None):
        if i == 'None':
            i = None
        if not self.smultiengine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.smultiengine.getResult(targets, clientID, block, i)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d 
    
    def xmlrpc_reset(self, request, clientID, block, targets):
        if not self.smultiengine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.smultiengine.reset(targets, clientID, block)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d 
    
    def xmlrpc_keys(self, request, clientID, block, targets):
        if not self.smultiengine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.smultiengine.keys(targets, clientID, block)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d  
    
    def xmlrpc_kill(self, request, clientID, block, targets, controller=False):
        if not self.smultiengine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.smultiengine.kill(targets, clientID, block, controller)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d
        
    def xmlrpc_pushSerialized(self, request, clientID, block, targets, binaryNS):
        if not self.smultiengine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            try:
                namespace = pickle.loads(binaryNS.data)
            except:
                d = defer.fail(failure.Failure())
            else:
                d = self.smultiengine.pushSerialized(targets, clientID, block, **namespace)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d  
    
    def xmlrpc_pullSerialized(self, request, clientID, block, targets, *keys):
        if not self.smultiengine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.smultiengine.pullSerialized(targets, clientID, block, *keys)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d    
    
    def xmlrpc_clearQueue(self, request, clientID, targets):
        if not self.smultiengine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.smultiengine.clearQueue(targets, client, True)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d   
    
    def xmlrpc_queueStatus(self, request, clientID, targets):
        if not self.smultiengine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.smultiengine.queueStatus(targets, clientID, True)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d  
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_getIDs(self, request):
        return self.multiEngine.getIDs()
     
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_scatter(self, request, clientID, block, targets, key, bseq, style='basic', flatten=False):
        if not self.smultiengine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            try:
                seq = pickle.loads(bseq.data)
            except:
                d = defer.fail(failure.Failure())
            else:
                d = self.smultiengine.scatter(targets, clientID, block, key, seq, style, flatten)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d      
    
    def xmlrpc_gather(self, request, clientID, block, targets, key, style='basic'):
        if not self.smultiengine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.smultiengine.gather(targets, clientID, block, key, style)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d     
    
    #---------------------------------------------------------------------------
    # Pending Deferred related methods
    #---------------------------------------------------------------------------            
    
    def xmlrpc_registerClient(self, request):
        """"""
        clientID = self.smultiengine.registerClient()
        return clientID
        
    def xmlrpc_unregisterClient(self, request, clientID):
        """"""
        try:
            self.smultiengine.unregisterClient(clientID)
        except error.InvalidClientID:
            f = failure.Failure()
            return self.packageFailure(f)
        else:
            return xmlrpc.Boolean(1)
            
    def xmlrpc_getPendingResult(self, request, clientID, resultID):
        """"""
        d = self.smultiengine.getPendingDeferred(clientID, resultID)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d
        
    def xmlrpc_getAllPendingDeferreds(self, clientID):
        """"""    
        d = self.smultiengine.getAllPendingDeferreds(clientID)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d        
    

components.registerAdapter(XMLRPCMultiEngineFromMultiEngine,
            MultiEngine, IXMLRPCMultiEngine)


class IXMLRPCMultiEngineFactory(Interface):
    pass
    
    
def XMLRPCServerFactoryFromMultiEngine(multiEngine):
    """Adapt a MultiEngine to a XMLRPCServerFactory."""
    s = server.Site(IXMLRPCMultiEngine(multiEngine))
    return channel.HTTPFactory(s)
    
    
components.registerAdapter(XMLRPCServerFactoryFromMultiEngine,
            MultiEngine, IXMLRPCMultiEngineFactory)
        

#-------------------------------------------------------------------------------
# The Client side of things
#-------------------------------------------------------------------------------

class XMLRPCMultiEngineClient(object):
    """XMLRPC based MultiEngine client that implements IMultiEngine.
    
    """
    
    implements(IMultiEngine)
    
    def __init__(self, server):
        self.server = server
        self.pendingDeferreds = {}
        self.clientID = self.server.getClientID()
    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------
        
    def handleReturn(self, r):
        """Remote methods should either return a pickled object or a pickled
        failure object prefixed with "FAILURE:"
        """
        try:
            return pickle.loads(r.data)
        except pickle.PickleError:
            raise error.KernelError("Could not unpickle returned object.")
    
    def fireCallbacks(self, results):
        for key , result in results.iteritems():
            if self.pendingDeferreds.has_key(key):
                self.pendingDeferreds[key].callback(result)
                del self.pendingDeferreds[key]
    
    
    #---------------------------------------------------------------------------
    # IXMLRPCMultiEngineClient
    #---------------------------------------------------------------------------
    
    def blockOn(self, d):
        for k,v in self.pendingDeferreds.iteritems():
            if d is v:
                (key, results) = self.handleReturn(self.server.blockOn(self.clientID, k))
                self.fireCallbacks(results)
                break
    
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
        
    def execute(self, targets, lines, block=False):
        (key, results) = self.handleReturn(self.server.execute(self.clientID, targets, lines, block))
        self.pendingDeferreds[key] = d = defer.Deferred()
        self.fireCallbacks(results)
        return d
    
    def executeAll(self, lines, block=False):
        return self.execute('all', lines, block)
    
    def push(self, targets, **namespace):
        try:
            binPackage = xmlrpc.Binary(pickle.dumps(namespace, 2))
        except:
            return defer.fail()
        else:
            (key, results) = self.handleReturn(self.server.push(self.clientID, targets, binPackage))
            self.pendingDeferreds[key] = d = defer.Deferred()
            self.fireCallbacks(results)
            return d
    
    def pushAll(self, **ns):
        return self.push('all', **ns)
    
    def pull(self, targets, *keys):
        (key, results) = self.handleReturn(self.server.pull(self.clientID, targets, *keys))
        self.pendingDeferreds[key] = d = defer.Deferred()
        self.fireCallbacks(results)
        return d
    
    def pullAll(self, *keys):
        return self.pull('all', *keys)
        
    def getResult(self, targets, i=None):
        if i is None: # This is because None cannot be marshalled by xml-rpc
            i = 'None'
        (key, results) = self.handleReturn(self.server.getResult(self.clientID, targets, i))
        self.pendingDeferreds[key] = d = defer.Deferred()
        self.fireCallbacks(results)
        return d
    
    def getResultAll(self, i=None):
        return self.getResult('all', i)
    
    def reset(self, targets):
        (key, results) = self.handleReturn(self.server.reset(self.clientID, targets))
        self.pendingDeferreds[key] = d = defer.Deferred()
        self.fireCallbacks(results)
        return d
    
    def resetAll(self):
        return self.reset('all')
    
    def keys(self, targets):
        (key, results) = self.handleReturn(self.server.keys(self.clientID, targets))
        self.pendingDeferreds[key] = d = defer.Deferred()
        self.fireCallbacks(results)
        return d
    
    def keysAll(self):
        return self.keys('all')
    
    def kill(self, targets, controller=False):
        (key, results) = self.handleReturn(self.server.kill(self.clientID, targets, controller))
        self.pendingDeferreds[key] = d = defer.Deferred()
        self.fireCallbacks(results)
        return d
    
    def killAll(self, controller=False):
        return self.kill('all', controller)
    
    def pushSerialized(self, targets, **namespace):
        try:
            binPackage = xmlrpc.Binary(pickle.dumps(namespace, 2))
        except:
            return defer.fail()
        else:
            (key, results) = self.handleReturn(self.server.pushSerialized(self.clientID, targets, binPackage))
            self.pendingDeferreds[key] = d = defer.Deferred()
            self.fireCallbacks(results)
            return d
    
    def pushSerializedAll(self, **namespace):
        return self.pushSerialized('all', **namespace)
    
    def pullSerialized(self, targets, *keys):
        (key, results) = self.handleReturn(self.server.pullSerialized(self.clientID, targets, *keys))
        self.pendingDeferreds[key] = d = defer.Deferred()
        self.fireCallbacks(results)
        return d
    
    def pullSerializedAll(self, *keys):
        return self.pullSerialized('all', *keys)
    
    def clearQueue(self, targets):
        (key, results) = self.handleReturn(self.server.clearQueue(self.clientID, targets))
        self.pendingDeferreds[key] = d = defer.Deferred()
        self.fireCallbacks(results)
        return d
    
    def clearQueueAll(self):
        return self.clearQueue('all')
    
    def queueStatus(self, targets):
        (key, results) = self.handleReturn(self.server.queueStatus(self.clientID, targets))
        self.pendingDeferreds[key] = d = defer.Deferred()
        self.fireCallbacks(results)
        return d
    
    def queueStatusAll(self):
        return self.queueStatus('all')
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def getIDs(self):
        (key, results) = self.handleReturn(self.server.getIDs(self.clientID))
        self.pendingDeferreds[key] = d = defer.Deferred()
        self.fireCallbacks(results)
        return d
    
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
    
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        try:
            bseq = xmlrpc.Binary(pickle.dumps(seq,2))
        except:
            return defer.Fail(failure.Failure())
        else:
            (key, results) = self.handleReturn(self.server.scatter(self.clientID, targets, key, bseq, style, flatten))
            self.pendingDeferreds[key] = d = defer.Deferred()
            self.fireCallbacks(results)
            return d
    
    def scatterAll(self, key, seq, style='basic', flatten=False):
        return self.scatter('all', key, seq, style, flatten)
    
    def gather(self, targets, key, style='basic'):
        (key, results) = self.handleReturn(self.server.gather(self.clientID, targets, key, style))
        self.pendingDeferreds[key] = d = defer.Deferred()
        self.fireCallbacks(results)
        return d
    
    def gatherAll(self, key, style='basic'):
        return self.gather('all', key, style)
    

    

components.registerAdapter(XMLRPCMultiEngineClient, 
        xmlrpclib.ServerProxy, IMultiEngine)
    
    
#-------------------------------------------------------------------------------
# The XMLRPC version of ConnectingMultiEngineClient
#-------------------------------------------------------------------------------

class XMLRPCConnectingMultiEngineClient(ConnectingMultiEngineClient):
    """XML-RPC version of the Connecting MultiEngineClient"""
    
    def connect(self):
        if not self.connected:
            addr = 'http://%s:%s/'%self.addr
            print "Connecting to ", addr
            self.multiengine = XMLRPCMultiEngineClient(xmlrpclib.Server(addr))
            self.connected = True
    
    def disconnect(self):
        if self.connected:
            print "Disconnecting from ", self.addr
            del self.multiengine
            self.multiengine = None
            self.connected = False
    
    def blockOn(self, d):
        self.multiengine.blockOn(d)
        return blockon.blockOn(d)
    
