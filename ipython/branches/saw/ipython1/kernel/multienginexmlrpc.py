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
from ipython1.kernel.multiengineclient import PendingResult
from ipython1.kernel.multiengineclient import InteractiveMultiEngineClient
from ipython1.kernel.xmlrpcutil import Transport

#-------------------------------------------------------------------------------
# The Controller side of things
#-------------------------------------------------------------------------------


BETWEEN_REQUESTS_TIMEOUT = 15*60


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
        
    def xmlrpc_getAllPendingResults(self, clientID):
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
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_execute(self, request, clientID, block, targets, lines):     
        d = self.smultiengine.execute(clientID, block, targets, lines)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d
    
    def xmlrpc_push(self, request, clientID, block, targets, binaryNS):
        try:
            namespace = pickle.loads(binaryNS.data)
        except:
            d = defer.fail(failure.Failure())
        else:
            d = self.smultiengine.push(clientID, block, targets, **namespace)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d
    
    def xmlrpc_pull(self, request, clientID, block, targets, *keys):
        d = self.smultiengine.pull(clientID, block, targets, *keys)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d
    
    def xmlrpc_getResult(self, request, clientID, block, targets, i=None):
        if i == 'None':
            i = None
        d = self.smultiengine.getResult(clientID, block, targets, i)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d 
    
    def xmlrpc_reset(self, request, clientID, block, targets):
        d = self.smultiengine.reset(clientID, block, targets)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d 
    
    def xmlrpc_keys(self, request, clientID, block, targets):
        d = self.smultiengine.keys(clientID, block, targets)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d  
    
    def xmlrpc_kill(self, request, clientID, block, targets, controller=False):
        d = self.smultiengine.kill(clientID, block, targets, controller)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d
        
    def xmlrpc_clearQueue(self, request, clientID, targets):
        d = self.smultiengine.clearQueue(clientID, True, targets)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d   
    
    def xmlrpc_queueStatus(self, request, clientID, targets):
        d = self.smultiengine.queueStatus(clientID, True, targets)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d  
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_getIDs(self, request):
        return self.smultiengine.getIDs()
     
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_scatter(self, request, clientID, block, targets, key, bseq, style='basic', flatten=False):
        try:
            seq = pickle.loads(bseq.data)
        except:
            d = defer.fail(failure.Failure())
        else:
            d = self.smultiengine.scatter(clientID, block, targets, key, seq, style, flatten)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d      
    
    def xmlrpc_gather(self, request, clientID, block, targets, key, style='basic'):
        d = self.smultiengine.gather(clientID, block, targets, key, style)
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
            return True
            
    def xmlrpc_getPendingResult(self, request, clientID, resultID, block):
        """"""
        d = self.smultiengine.getPendingDeferred(clientID, resultID, block)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d
        
    def xmlrpc_getAllPendingResults(self, request, clientID):
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
    cf = channel.HTTPFactory(s, betweenRequestsTimeOut=BETWEEN_REQUESTS_TIMEOUT)
    return cf

components.registerAdapter(XMLRPCServerFactoryFromMultiEngine,
            MultiEngine, IXMLRPCMultiEngineFactory)
        

#-------------------------------------------------------------------------------
# The Client side of things
#-------------------------------------------------------------------------------

class XMLRPCMultiEngineClient(object):
    """XMLRPC based MultiEngine client that implements IMultiEngine.
    
    """
    
    def __init__(self, addr):
        self.addr = addr
        self.url = 'http://%s:%s/' % self.addr
        self.server = xmlrpclib.ServerProxy(self.url, transport=Transport(), 
            verbose=0)
        self.clientID = None
        self.block = True

    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------
        
    def _reallyBlock(self, block=None):
        if block is None:
            return self.block
        else:
            if block in (True, False):
                return block
            else:
                raise ValueError("block must be True or False")
        
    def _executeRemoteMethod(self, f, *args):
        try:
            rawResult = f(*args)
            result = self._unpackageResult(rawResult)
        except error.InvalidClientID:
            self._getClientID()
            rawResult = f(*args)
            result = self._unpackageResult(rawResult)
        return result

    def _unpackageResult(self, result):
        result = pickle.loads(result.data)
        return self._returnOrRaise(result)
        
    def _returnOrRaise(self, result):
        if isinstance(result, failure.Failure):
            result.raiseException()
        else:
            return result
        
    def _checkClientID(self):
        if self.clientID is None:
            self._getClientID()
            
    def _getClientID(self):
        clientID = self.server.registerClient()
        self.clientID = clientID
    
    #---------------------------------------------------------------------------
    # Pending results related methods
    #--------------------------------------------------------------------------- 
    
    def getPendingResult(self, resultID, block=True):
        self._checkClientID()
        return self._executeRemoteMethod(self.server.getPendingResult,
            self.clientID, resultID, block)
        
    def getAllPendingResults(self):
        self._checkClientID()
        result = self._executeRemoteMethod(self.server.getAllPendingResults, self.clientID)
        for r in result:
            if isinstance(r, failure.Failure):
                r.raiseException()
        if len(result) == 1:
            result = result[0]
        return result
        
    def barrier(self):
        self._checkClientID()
        result = self._executeRemoteMethod(self.server.getAllPendingResults, self.clientID)
        for r in result:
            if isinstance(r, failure.Failure):
                r.raiseException() 
        
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
        
    def execute(self, targets, lines, block=None):
        self._checkClientID()
        localBlock = self._reallyBlock(block)
        result = self._executeRemoteMethod(self.server.execute, self.clientID, localBlock, targets, lines)
        if not localBlock:
            result = PendingResult(self, result)
        return result
    
    def executeAll(self, lines, block=None):
        return self.execute('all', lines, block)
    
    def push(self, targets, **namespace):
        self._checkClientID()
        binPackage = xmlrpc.Binary(pickle.dumps(namespace, 2))
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod(self.server.push, self.clientID, localBlock, targets, binPackage)
        if not localBlock:
            result = PendingResult(self, result)
        return result
                
    def pushAll(self, **ns):
        return self.push('all', **ns)
    
    def pull(self, targets, *keys):
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod(self.server.pull, self.clientID, localBlock, targets, *keys)
        if not localBlock:
            result = PendingResult(self, result)
        return result
    
    def pullAll(self, *keys):
        return self.pull('all', *keys)
        
    def getResult(self, targets, i=None):
        if i is None: # This is because None cannot be marshalled by xml-rpc
            i = 'None'
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod(self.server.getResult, self.clientID, localBlock, targets, i)
        if not localBlock:
            result = PendingResult(self, result)
        return result            
         
    def getResultAll(self, i=None):
        return self.getResult('all', i)
    
    def reset(self, targets):
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod(self.server.reset, self.clientID, localBlock, targets)
        if not localBlock:
            result = PendingResult(self, result)
        return result    
        
    def resetAll(self):
        return self.reset('all')
    
    def keys(self, targets):
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod(self.server.keys, self.clientID, localBlock, targets)
        if not localBlock:
            result = PendingResult(self, result)
        return result 
          
    def keysAll(self):
        return self.keys('all')
    
    def kill(self, targets, controller=False):
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod(self.server.kill, self.clientID, localBlock, targets, controller)
        if not localBlock:
            result = PendingResult(self, result)
        return result
    
    def killAll(self, controller=False):
        return self.kill('all', controller)
        
    def clearQueue(self, targets):
        self._checkClientID()
        result = self._executeRemoteMethod(self.server.clearQueue, self.clientID, targets)
        return result
        
    def clearQueueAll(self):
        return self.clearQueue('all')
    
    def queueStatus(self, targets):
        self._checkClientID()
        result = self._executeRemoteMethod(self.server.queueStatus, self.clientID, targets)
        return result
    
    def queueStatusAll(self):
        return self.queueStatus('all')
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def getIDs(self):
        return self.server.getIDs()
    
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
    
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        self._checkClientID()
        bseq = xmlrpc.Binary(pickle.dumps(seq,2))
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod(self.server.scatter, self.clientID, 
            localBlock, targets, key, bseq, style, flatten)
        if not localBlock:
            result = PendingResult(self, result)
        return result
        
    def scatterAll(self, key, seq, style='basic', flatten=False):
        return self.scatter('all', key, seq, style, flatten)
    
    def gather(self, targets, key, style='basic'):
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod(self.server.gather, self.clientID, 
            localBlock, targets, key, style)
        if not localBlock:
            result = PendingResult(self, result)
        return result        
        
    def gatherAll(self, key, style='basic'):
        return self.gather('all', key, style)


class XMLRPCInteractiveMultiEngineClient(XMLRPCMultiEngineClient, InteractiveMultiEngineClient):
    
    def __init__(self, addr):
        XMLRPCMultiEngineClient.__init__(self, addr)

    
    
