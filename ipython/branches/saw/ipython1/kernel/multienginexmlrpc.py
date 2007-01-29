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
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
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
# from twisted.application import 
from twisted.internet import reactor, defer
from twisted.python import components
from twisted.python.failure import Failure

from twisted.spread import pb

from twisted.web2 import xmlrpc, server, channel
# import ipython1.kernel.pbconfig
from ipython1.kernel import error
from ipython1.kernel.multiengine import MultiEngine, IMultiEngine
from ipython1.kernel.blockon import blockOn
from ipython1.kernel.util import gatherBoth


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
    
    def packageFailure(self, f):
        f.cleanFailure()
        pString = pickle.dumps(f)
        return "FAILURE:"+pString
    
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_execute(self, request, targets, lines):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.execute(targets, lines)
        return d.addCallbacks(pickle.dumps, self.packageFailure)
    
    def xmlrpc_push(self, request, targets, pNamespace):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            try:
                namespace = pickle.loads(pNamespace)
            except:
                d = defer.fail()
            else:
                d = self.multiEngine.push(targets, **namespace)
        return d.addCallbacks(pickle.dumps, self.packageFailure)
    
    def xmlrpc_pull(self, request, targets, *keys):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.pull(targets, *keys)
        return d.addCallbacks(pickle.dumps, self.packageFailure)
    
    def xmlrpc_getResult(self, request, targets, i=None):
        if i == -1:
            i = None
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.getResult(targets, i)
        return d.addCallbacks(pickle.dumps, self.packageFailure)
    
    def xmlrpc_reset(self, request, targets):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.reset(targets)
        return d.addCallbacks(pickle.dumps, self.packageFailure)
    
    def xmlrpc_keys(self, request, targets):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.keys(targets)
        return d.addCallbacks(pickle.dumps, self.packageFailure)
    
    def xmlrpc_kill(self, request, targets, controller=False):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.kill(targets, controller)
        return d.addCallbacks(pickle.dumps, self.packageFailure)
        
    def xmlrpc_pushSerialized(self, request, targets, pNamespace):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            try:
                namespace = pickle.loads(pNamespace)
            except:
                d = defer.fail(Failure())
            else:
                d = self.multiEngine.pushSerialized(targets, **namespace)
        return d.addCallbacks(pickle.dumps, self.packageFailure)
    
    def xmlrpc_pullSerialized(self, request, targets, *keys):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.pullSerialized(targets, *keys)
        return d.addCallbacks(pickle.dumps, self.packageFailure)
    
    def xmlrpc_clearQueue(self, request, targets):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.clearQueue(targets)
        return d.addCallbacks(pickle.dumps, self.packageFailure)
    
    def xmlrpc_queueStatus(self, request, targets):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.queueStatus(targets)
        return d.addCallbacks(pickle.dumps, self.packageFailure)
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_getIDs(self, request):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.getIDs()
        return d.addCallbacks(pickle.dumps, self.packageFailure)
    
    def xmlrpc_verifyTargets(self, request, targets):
        return self.multiEngine.verifyTargets(targets)
    
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_scatter(self, request, targets, key, pseq, style='basic', flatten=False):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            try:
                seq = pickle.loads(pseq)
            except:
                d = defer.fail(Failure())
            else:
                d = self.multiEngine.scatter(targets, key, seq, style, flatten)
        return d.addCallbacks(pickle.dumps, self.packageFailure)
    
    def xmlrpc_gather(self, request, targets, key, style='basic'):
        if not self.multiEngine.verifyTargets(targets):
            d = defer.fail(error.InvalidEngineID(str(targets)))
        else:
            d = self.multiEngine.gather(targets, key, style)
            d.addCallback(pickle.dumps)
        return d.addCallbacks(pickle.dumps, self.packageFailure)
    

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
    
    One could have this inherit from pb.Referencable and implement xmlrpc_foo
    methods to allow the MultiEngine to call methods on this class.  This is
    how the old notification system worked.
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
        
        if r.startswith('FAILURE:'):
            r = r[8:]
        try:
            result = pickle.loads(r)
        except pickle.PickleError:
            return defer.fail(error.KernelError("Could not unpickle return."))
        else:
            if isinstance(result, Failure):
                # Raise the exception if it is a failure
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
            package = pickle.dumps(namespace)
        except:
            return Failure()
        else:
            return self.handleReturn(self.server.push(targets, package))
    
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
            package = pickle.dumps(namespace)
        except:
            return Failure()
        else:
            return self.handleReturn(self.server.pushSerialized(targets, package))
    
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
            pseq = pickle.dumps(seq)
        except:
            return Failure()
        else:
            return self.handleReturn(self.server.scatter(targets, key, pseq, style, flatten))
    
    def scatterAll(self, key, seq, style='basic', flatten=False):
        return self.scatter('all', key, seq, style, flatten)
    
    def gather(self, targets, key, style='basic'):
        r = self.handleReturn(self.server.gather(targets, key, style='basic'))
        if not isinstance(r, Failure):
            return pickle.loads(r)
        return r
    
    def gatherAll(self, key, style='basic'):
        return self.gather('all', key, style)
    

components.registerAdapter(XMLRPCMultiEngineClient, 
        xmlrpclib.Server, IMultiEngine)
    
    
#-------------------------------------------------------------------------------
# The XMLRPC version of RemoteController
#-------------------------------------------------------------------------------

class RemoteController(object):
    """A high-level XMLRPCRemoteController.
    Note: The connect/disconnect methods are not yet fully implemented.  
    They are leftover from PB RemoteController
    """
    
    def __init__(self, addr):
        """addr is a URL of the form: 'http://ipaddress:port/"""
        self.addr = addr
        if self.addr[-1] != '/': # it requires the slash at the moment
            self.addr += '/'
        self.multiengine = None
        self.pendingDeferreds = []
        self.connected = False
    
    def connect(self):
        if not self.connected:
            print "Connecting to ", self.addr
            self.multiengine = XMLRPCMultiEngineClient(xmlrpclib.Server(self.addr))
            self.connected = True
    
    def disconnect(self):
        # disconnections are not handled
        self.handleDisconnect(None)
    
    def handleDisconnect(self, thingy):
        print "Disconnecting from ", self.addr
        self.connected = False
        del self.multiengine
        self.multiengine = None
    
    #---------------------------------------------------------------------------
    # Interface methods
    #---------------------------------------------------------------------------
    
    def execute(self, targets, lines):
        self.connect()
        return blockOn(self.multiengine.execute(targets, lines))
    
    def executeAll(self, lines):
        return self.execute('all', lines)
    
    def push(self, targets, **namespace):
        self.connect()
        return blockOn(self.multiengine.push(targets, **namespace))
    
    def pushAll(self, **namespace):
        return self.push('all', **namespace)
    
    def pull(self, targets, *keys):
        self.connect()
        return blockOn(self.multiengine.pull(targets, *keys))
    
    def pullAll(self, *keys):
        return self.pull('all', *keys)
    
    def getResult(self, targets, i=None):
        self.connect()
        return blockOn(self.multiengine.getResult(targets, i))
    
    def getResultAll(self, i=None):
        return self.getResult('all', i)
    
    def reset(self, targets):
        self.connect()
        return blockOn(self.multiengine.reset(targets))
    
    def resetAll(self):
        return self.reset('all')
    
    def keys(self, targets):
        self.connect()
        return blockOn(self.multiengine.keys(targets))
    
    def keysAll(self):
        return self.keys('all')
    
    def kill(self, targets, controller=False):
        self.connect()
        return blockOn(self.multiengine.kill(targets, controller))
    
    def killAll(self, controller=False):
        return self.kill('all', controller)
    
    def pushSerialized(self, targets, **namespace):
        self.connect()
        return blockOn(self.multiengine.pushSerialized(targets, **namespace))
    
    def pushSerializedAll(self, **namespace):
        return self.pushSerialized('all', **namespace)
    
    def pullSerialized(self, targets, *keys):
        self.connect()
        return blockOn(self.multiengine.pullSerialized(targets, *keys))
    
    def pullSerializedAll(self, *keys):
        return self.pullSerialized('all', *keys)
    
    def clearQueue(self, targets):
        self.connect()
        return blockOn(self.multiengine.clearQueue(targets))
    
    def clearQueueAll(self):
        return self.clearQueue('all')
    
    def queueStatus(self, targets):
        self.connect()
        return blockOn(self.multiengine.queueStatus(targets))
    
    def queueStatusAll(self):
        return self.queueStatus('all')
    
    def getIDs(self):
        self.connect()
        return blockOn(self.multiengine.getIDs())
    
    def verifyTargets(self, targets):
        self.connect()
        return blockOn(self.multiengine.verifyTargets(targets))
    
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        self.connect()
        return blockOn(self.multiengine.scatter(targets, key, seq, style, flatten))
    
    def scatterAll(self, key, seq, style='basic', flatten=False):
        return self.scatter('all', key, seq, style, flatten)
    
    def gather(self, targets, key, style='basic'):
        self.connect()
        return blockOn(self.multiengine.gather(targets, key, style))
    
    def gatherAll(self, key, style='basic'):
        return self.gather('all', key, style)
