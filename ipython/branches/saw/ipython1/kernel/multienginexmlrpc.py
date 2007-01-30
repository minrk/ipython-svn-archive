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
from twisted.python import components
from twisted.python.failure import Failure

from twisted.web2 import xmlrpc, server, channel

from ipython1.kernel import error
from ipython1.kernel.multiengine import MultiEngine, IMultiEngine
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
            
    def xmlrpc_execute(request,targets, lines):
        """"""
        
    def xmlrpc_push(request,targets, namespace):
        """"""
        
    def xmlrpc_pull(request,targets, *keys):
        """"""
        
    def xmlrpc_getResult(request,targets, i=None):
        """"""
        
    def xmlrpc_reset(request,targets):
        """"""
        
    def xmlrpc_keys(request,targets):
        """"""
        
    def xmlrpc_kill(request,targets, controller=False):
        """"""
        
    def xmlrpc_pushSerialized(request,targets, namespace):
        """"""
        
    def xmlrpc_pullSerialized(request,targets, *keys):
        """"""
        
    def xmlrpc_clearQueue(request,targets):
        """"""
        
    def xmlrpc_queueStatus(request,targets):
        """"""
        
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
        
    def xmlrpc_getIDs(request):
        """"""
        
    def xmlrpc_verifyTargets(request,targets):
        """"""
    
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
        
    def xmlrpc_scatter(request,targets, key, seq, style='basic', flatten=False):
        """"""
        
    def xmlrpc_gather(request,targets, key, style='basic'):
        """"""
                
        
class XMLRPCMultiEngineFromMultiEngine(xmlrpc.XMLRPC):
    """XML-RPC attachmeot for controller.
    
    See IXMLRPCMultiEngine and IMultiEngine (and its children) for documentation. 
    """
    implements(IXMLRPCMultiEngine)
    
    addSlash = True
    
    def __init__(self, multiEngine):
        xmlrpc.XMLRPC.__init__(self)
        self.multiEngine = multiEngine
        
    
    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------
    
    def packageReturn(self, r):
        return xmlrpc.Binary(pickle.dumps(r,2))
    
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_execute(self, request, targets, lines):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.execute(targets, lines)
        return d.addBoth(self.packageReturn)
    
    def xmlrpc_push(self, request, targets, binaryNS):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            try:
                namespace = pickle.loads(binaryNS.data)
            except:
                d = defer.fail()
            else:
                d = self.multiEngine.push(targets, **namespace)
        return d.addBoth(self.packageReturn)
    
    def xmlrpc_pull(self, request, targets, *keys):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.pull(targets, *keys)
        return d.addBoth(self.packageReturn)
    
    def xmlrpc_getResult(self, request, targets, i=None):
        if i == -1:
            i = None
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.getResult(targets, i)
        return d.addBoth(self.packageReturn)
    
    def xmlrpc_reset(self, request, targets):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.reset(targets)
        return d.addBoth(self.packageReturn)
    
    def xmlrpc_keys(self, request, targets):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.keys(targets)
        return d.addBoth(self.packageReturn)
    
    def xmlrpc_kill(self, request, targets, controller=False):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.kill(targets, controller)
        return d.addBoth(self.packageReturn)
        
    def xmlrpc_pushSerialized(self, request, targets, binaryNS):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            try:
                namespace = pickle.loads(binaryNS.data)
            except:
                d = defer.fail(Failure())
            else:
                d = self.multiEngine.pushSerialized(targets, **namespace)
        return d.addBoth(self.packageReturn)
    
    def xmlrpc_pullSerialized(self, request, targets, *keys):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.pullSerialized(targets, *keys)
        return d.addBoth(self.packageReturn)
    
    def xmlrpc_clearQueue(self, request, targets):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.clearQueue(targets)
        return d.addBoth(self.packageReturn)
    
    def xmlrpc_queueStatus(self, request, targets):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.queueStatus(targets)
        return d.addBoth(self.packageReturn)
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_getIDs(self, request):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.getIDs()
        return d.addBoth(self.packageReturn)
    
    def xmlrpc_verifyTargets(self, request, targets):
        return self.multiEngine.verifyTargets(targets)
    
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_scatter(self, request, targets, key, bseq, style='basic', flatten=False):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            try:
                seq = pickle.loads(bseq.data)
            except:
                d = defer.fail(Failure())
            else:
                d = self.multiEngine.scatter(targets, key, seq, style, flatten)
        return d.addBoth(self.packageReturn)
    
    def xmlrpc_gather(self, request, targets, key, style='basic'):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.gather(targets, key, style)
            # d.addCallback(pickle.dumps, 2)
        return d.addBoth(self.packageReturn)
    

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
        
    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------
        
    def handleReturn(self, r):
        """Remote methods should either return a pickled object or a pickled
        failure object prefixed with "FAILURE:"
        """
        assert isinstance(r, xmlrpc.Binary), "Should return xmlrpc Binary object"
        try:
            result = pickle.loads(r.data)
        except pickle.PickleError:
            return defer.fail(error.KernelError("Could not unpickle return."))
        else:
            if isinstance(result, Failure):
                return defer.fail(result)
            return defer.succeed(result)
    
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
        
    def execute(self, targets, lines):
        return self.handleReturn(self.server.execute(targets, lines))
    
    def executeAll(self, lines):
        return self.execute('all', lines)
    
    def push(self, targets, **namespace):
        try:
            binPackage = xmlrpc.Binary(pickle.dumps(namespace, 2))
        except:
            return defer.fail()
        else:
            return self.handleReturn(self.server.push(targets, binPackage))
    
    def pushAll(self, **ns):
        return self.push('all', **ns)
    
    def pull(self, targets, *keys):
        return self.handleReturn(self.server.pull(targets, *keys))
    
    def pullAll(self, *keys):
        return self.pull('all', *keys)
        
    def getResult(self, targets, i=None):
        if i is None: # This is because None cannot be marshalled by xml-rpc
            i = -1
        return self.handleReturn(self.server.getResult(targets, i))
    
    def getResultAll(self, i=None):
        if i is None: # This is because None cannot be marshalled by xml-rpc
            i = -1
        return self.getResult('all', i)
    
    def reset(self, targets):
        return self.handleReturn(self.server.reset(targets))
    
    def resetAll(self):
        return self.reset('all')
    
    def keys(self, targets):
        return self.handleReturn(self.server.keys(targets))
    
    def keysAll(self):
        return self.keys('all')
    
    def kill(self, targets, controller=False):
        return self.handleReturn(self.server.kill(targets, controller))
    
    def killAll(self, controller=False):
        return self.kill('all', controller)
    
    def pushSerialized(self, targets, **namespace):
        try:
            binPackage = xmlrpc.Binary(pickle.dumps(namespace, 2))
        except:
            return defer.fail()
        else:
            return self.handleReturn(self.server.pushSerialized(targets, binPackage))
    
    def pushSerializedAll(self, **namespace):
        return self.pushSerialized('all', **namespace)
    
    def pullSerialized(self, targets, *keys):
        return self.handleReturn(self.server.pullSerialized(targets, *keys))
    
    def pullSerializedAll(self, *keys):
        return self.pullSerialized('all', *keys)
    
    def clearQueue(self, targets):
        return self.handleReturn(self.server.clearQueue(targets))
    
    def clearQueueAll(self):
        return self.clearQueue('all')
    
    def queueStatus(self, targets):
        return self.handleReturn(self.server.queueStatus(targets))
    
    def queueStatusAll(self):
        return self.queueStatus('all')
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def getIDs(self):
        return self.handleReturn(self.server.getIDs())
    
    def verifyTargets(self, targets):
        return self.handleReturn(self.server.verifyTargets(targets))
    
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
    
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        try:
            bseq = xmlrpc.Binary(pickle.dumps(seq,2))
        except:
            return Failure()
        else:
            return self.handleReturn(self.server.scatter(targets, key, bseq, style, flatten))
    
    def scatterAll(self, key, seq, style='basic', flatten=False):
        return self.scatter('all', key, seq, style, flatten)
    
    def gather(self, targets, key, style='basic'):
        r = self.handleReturn(self.server.gather(targets, key, style))
        return r
    
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
    
