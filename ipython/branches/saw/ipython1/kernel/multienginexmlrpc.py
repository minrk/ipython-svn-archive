# encoding: utf-8
# -*- test-case-name: ipython1.test.test_multienginexmlrpc -*-
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
import xmlrpclib

from zope.interface import Interface, implements
from twisted.internet import defer
from twisted.python import components, failure

from ipython1.external.twisted.web2 import xmlrpc, server, channel

from ipython1.kernel import error, blockon
from ipython1.kernel.multiengine import MultiEngine, IMultiEngine
from ipython1.kernel.multiengine import ISynchronousMultiEngine
from ipython1.kernel.multiengineclient import PendingResult
from ipython1.kernel.multiengineclient import ResultList, QueueStatusList
from ipython1.kernel.multiengineclient import wrapResultList
from ipython1.kernel.multiengineclient import InteractiveMultiEngineClient
from ipython1.kernel.xmlrpcutil import Transport

#-------------------------------------------------------------------------------
# The Controller side of things
#-------------------------------------------------------------------------------


# This sets the timeout that twisted/web2 uses between requests.
BETWEEN_REQUESTS_TIMEOUT = 15*60


class IXMLRPCMultiEngine(Interface):
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
        """Clear the queue on targets.
        
        This method always blocks.  This means that it will always waits for
        the queues to be cleared before returning.  This method will never
        return the id of a pending deferred.
        """
        
    def xmlrpc_queueStatus(request, clientID, targets):
        """Get the queue status on targets.
        
        This method always blocks.  This means that it will always return
        the queues status's.  This method will never return the id of a pending 
        deferred.    
        """
        
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
        
    def xmlrpc_getIDs(request):
        """Get the ids of the registered engines.
        
        This method always blocks.
        """
        
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


class XMLRPCMultiEngineFromMultiEngine(xmlrpc.XMLRPC):
    """Adapt `IMultiEngine` -> `ISynchronousMultiEngine` -> `IXMLRPCMultiEngine`.
    """
    
    implements(IXMLRPCMultiEngine)
    
    addSlash = True
    
    def __init__(self, multiengine):
        xmlrpc.XMLRPC.__init__(self)
        # Adapt the raw multiengine to `ISynchronousMultiEngine` before saving
        # it.  This allow this class to do two adaptation steps.
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
    
    @packageResult
    def xmlrpc_execute(self, request, clientID, block, targets, lines):     
        return self.smultiengine.execute(clientID, block, targets, lines)
    
    @packageResult    
    def xmlrpc_push(self, request, clientID, block, targets, binaryNS):
        try:
            namespace = pickle.loads(binaryNS.data)
        except:
            d = defer.fail(failure.Failure())
        else:
            d = self.smultiengine.push(clientID, block, targets, **namespace)
        return d

    @packageResult
    def xmlrpc_pull(self, request, clientID, block, targets, *keys):
        return self.smultiengine.pull(clientID, block, targets, *keys)
    
    @packageResult
    def xmlrpc_getResult(self, request, clientID, block, targets, i=None):
        if i == 'None':
            i = None
        return self.smultiengine.getResult(clientID, block, targets, i)
    
    @packageResult
    def xmlrpc_reset(self, request, clientID, block, targets):
        return self.smultiengine.reset(clientID, block, targets)
    
    @packageResult
    def xmlrpc_keys(self, request, clientID, block, targets):
        return self.smultiengine.keys(clientID, block, targets)
    
    @packageResult
    def xmlrpc_kill(self, request, clientID, block, targets, controller=False):
        return self.smultiengine.kill(clientID, block, targets, controller)

    @packageResult
    def xmlrpc_clearQueue(self, request, clientID, targets):
        return self.smultiengine.clearQueue(clientID, True, targets)

    @packageResult
    def xmlrpc_queueStatus(self, request, clientID, targets):
        return self.smultiengine.queueStatus(clientID, True, targets)
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_getIDs(self, request):
        return self.smultiengine.getIDs()
     
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
    
    @packageResult
    def xmlrpc_scatter(self, request, clientID, block, targets, key, bseq, style='basic', flatten=False):
        try:
            seq = pickle.loads(bseq.data)
        except:
            d = defer.fail(failure.Failure())
        else:
            d = self.smultiengine.scatter(clientID, block, targets, key, seq, style, flatten)
        return d      
    
    @packageResult
    def xmlrpc_gather(self, request, clientID, block, targets, key, style='basic'):
        return self.smultiengine.gather(clientID, block, targets, key, style)
    
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
            
    @packageResult
    def xmlrpc_getPendingResult(self, request, clientID, resultID, block):
        """"""
        return self.smultiengine.getPendingDeferred(clientID, resultID, block)
        
    @packageResult
    def xmlrpc_getAllPendingResults(self, request, clientID):
        """"""    
        return self.smultiengine.getAllPendingDeferreds(clientID)
    

# The __init__ method of `XMLRPCMultiEngineFromMultiEngine` first adapts the
# `IMultiEngine` to `ISynchronousMultiEngine` so this is actually doing a
# two phase adaptation.
components.registerAdapter(XMLRPCMultiEngineFromMultiEngine,
            IMultiEngine, IXMLRPCMultiEngine)


class IXMLRPCMultiEngineFactory(Interface):
    pass
    
    
def XMLRPCServerFactoryFromMultiEngine(multiengine):
    """Adapt a MultiEngine to a XMLRPCServerFactory."""
    s = server.Site(IXMLRPCMultiEngine(multiengine))
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

class XMLRPCMultiEngineClient(object):
    """Client that talks to a IMultiEngine adapted controller over XML-RPC.
    
    This class will usually be alias to RemoteController so create one like 
    this:
    
    >>> rc = RemoteController(('myhost.work.com', 10105))
    
    This class has a attribute named block that controls how most methods
    work.  If block=True (default) all methods will actually block until
    their action has been completed.  Then they will return their result
    or raise any Exceptions.  If block=False, the method will simply
    return a `PendingResult` object whose `getResult` method can then be
    used to later retrieve the result.
    """
    
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
        self._server = xmlrpclib.ServerProxy(self.url, transport=Transport(), 
            verbose=0)
        self._clientID = None
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
        if self._clientID is None:
            self._getClientID()
            
    def _getClientID(self):
        clientID = self._server.registerClient()
        self._clientID = clientID

    def _getPendingResult(self, resultID, block=True):
        self._checkClientID()
        return self._executeRemoteMethod(self._server.getPendingResult,
            self._clientID, resultID, block)
    
    #---------------------------------------------------------------------------
    # Methods to help manage pending results
    #--------------------------------------------------------------------------- 
     
    def barrier(self):
        """Synchronize flush all PendingResults.
        
        This method is a synchronization primitive that waits for all existing
        PendingResult that a controller knows about to complete and then 
        flushes them.  More specifically, three things happen:
        
        * Wait for all PendingResults on a controller to complete.
        * Raise any Exceptions that occured in the PendingResults.
        * Flush the PendingResults from the controller.
        
        If there are multiple Exceptions, only the first is raised.  
        
        The flush step is extremely important!  If have a PendingResult object
        and then call barrier, further calls to PendingResult.getResult will
        fail as the controller no longer knows about the PendingResult:
        
        >>> pr = rc.executeAll('a=5',block=False)
        >>> rc.barrier()
        >>> pr.getResult()           # This will fail as pr has been flushed.
        
        This method should be used when you need to make sure that all
        PendingResults have completed and check for errors.  If you actually
        need to access the results of those PendingResults, you should not
        call barrier.  Instead, call PendingResult.getResult on each object.
        """
        self._checkClientID()
        # Optimize to not bring back all results
        result = self._executeRemoteMethod(self._server.getAllPendingResults, self._clientID)
        for r in result:
            if isinstance(r, failure.Failure):
                r.raiseException()
        
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
        
    def execute(self, targets, lines, block=None):
        """Execute lines of code on targets and possibly block.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `getIDs` to see
                a list of currently available engines. 
            lines : str
                A string of Python code to execute.
            block : boolean
                Should I block or not.  If block=True, wait for the action to
                complete and return the result.  If block=False, return a
                `PendingResult` object that can be used to later get the
                result.  If block is not specified, the block attribute 
                will be used instead.
            
        :Returns: A list of dictionaries with the stdin/stdout/stderr of the 
        command on each targets.
        """
        self._checkClientID()
        localBlock = self._reallyBlock(block)
        result = self._executeRemoteMethod(self._server.execute, self._clientID, localBlock, targets, lines)
        if not localBlock:
            result = PendingResult(self, result)
            result.addCallback(wrapResultList)
        else:
            result = ResultList(result)
        return result
    
    def executeAll(self, lines, block=None):
        """Execute lines of code on all targets.
        
        See the docstring for `execute` for full details.
        """
        return self.execute('all', lines, block)
    
    def push(self, targets, **namespace):
        """Push Python objects to engines by key.
        
        This method takes all key/value pairs passed in as keyword arguments
        and pushes them to the engines specified in targets.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `getIDs` to see
                a list of currently available engines.
            namespace : dict
                The keyword arguments of that contain the key, value pairs
                that will be pushed.
                
        Examples
        ========
        
        >>> rc.push('all', a=5)    # pushes 5 to all engines as 'a'
        >>> rc.push(0, b=30)       # pushes 30 to 0 as 'b'
        """
        self._checkClientID()
        binPackage = xmlrpc.Binary(pickle.dumps(namespace, 2))
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod(self._server.push, self._clientID, localBlock, targets, binPackage)
        if not localBlock:
            result = PendingResult(self, result)
        return result
                
    def pushAll(self, **ns):
        return self.push('all', **ns)
    
    def pull(self, targets, *keys):
        """
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `getIDs` to see
                a list of currently available engines.
        """
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod(self._server.pull, self._clientID, localBlock, targets, *keys)
        if not localBlock:
            result = PendingResult(self, result)
        return result
    
    def pullAll(self, *keys):
        return self.pull('all', *keys)
        
    def getResult(self, targets, i=None):
        """
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `getIDs` to see
                a list of currently available engines.
        """
        if i is None: # This is because None cannot be marshalled by xml-rpc
            i = 'None'
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod(self._server.getResult, self._clientID, localBlock, targets, i)
        if not localBlock:
            result = PendingResult(self, result)
            result.addCallback(wrapResultList)
        else:
            result = ResultList(result)
        return result
         
    def getResultAll(self, i=None):
        return self.getResult('all', i)
    
    def reset(self, targets):
        """
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `getIDs` to see
                a list of currently available engines.
        """
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod(self._server.reset, self._clientID, localBlock, targets)
        if not localBlock:
            result = PendingResult(self, result)
        return result    
        
    def resetAll(self):
        return self.reset('all')
    
    def keys(self, targets):
        """List all the variable names defined on each engine.
        
        :Parameters:
            targets : int, list or 'all'
                The engine ids the action will apply to.  Call `getIDs` to see
                a list of currently available engines.
        
        :Returns: A list of the variables names on each engine.
        """
        
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod(self._server.keys, self._clientID, localBlock, targets)
        if not localBlock:
            result = PendingResult(self, result)
        return result 
          
    def keysAll(self):
        return self.keys('all')
    
    def kill(self, targets, controller=False):
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod(self._server.kill, self._clientID, localBlock, targets, controller)
        if not localBlock:
            result = PendingResult(self, result)
        return result
    
    def killAll(self, controller=False):
        return self.kill('all', controller)
        
    def clearQueue(self, targets):
        self._checkClientID()
        result = self._executeRemoteMethod(self._server.clearQueue, self._clientID, targets)
        return result
        
    def clearQueueAll(self):
        return self.clearQueue('all')
    
    def queueStatus(self, targets):
        self._checkClientID()
        result = self._executeRemoteMethod(self._server.queueStatus, self._clientID, targets)
        return QueueStatusList(result)
    
    def queueStatusAll(self):
        return self.queueStatus('all')
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def getIDs(self):
        return self._server.getIDs()
    
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
    
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        self._checkClientID()
        bseq = xmlrpc.Binary(pickle.dumps(seq,2))
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod(self._server.scatter, self._clientID, 
            localBlock, targets, key, bseq, style, flatten)
        if not localBlock:
            result = PendingResult(self, result)
        return result
        
    def scatterAll(self, key, seq, style='basic', flatten=False):
        return self.scatter('all', key, seq, style, flatten)
    
    def gather(self, targets, key, style='basic'):
        self._checkClientID()
        localBlock = self._reallyBlock()
        result = self._executeRemoteMethod(self._server.gather, self._clientID, 
            localBlock, targets, key, style)
        if not localBlock:
            result = PendingResult(self, result)
        return result        
        
    def gatherAll(self, key, style='basic'):
        return self.gather('all', key, style)


class XMLRPCInteractiveMultiEngineClient(XMLRPCMultiEngineClient, InteractiveMultiEngineClient):
    
    __doc__ = XMLRPCMultiEngineClient.__doc__
    
    def __init__(self, addr):
        XMLRPCMultiEngineClient.__init__(self, addr)
        InteractiveMultiEngineClient.__init__(self)

    __init__.__doc__ = XMLRPCMultiEngineClient.__init__.__doc__
    
