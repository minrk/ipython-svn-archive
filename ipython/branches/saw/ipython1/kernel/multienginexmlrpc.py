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
from twisted.internet import reactor
from twisted.python import components
from twisted.python.failure import Failure

from twisted.spread import pb

from twisted.web2 import xmlrpc, server, channel
# import ipython1.kernel.pbconfig
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
        
    def xmlrpc_push(request,targets, **namespace):
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
        
    def xmlrpc_pushSerialized(request,targets, **namespace):
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
        self.multiEngine = multiEngine
    
    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------
    
    def checkReturns(self, rlist):
        for r in rlist:
            if isinstance(r, (Failure, Exception)):
                rlist[rlist.index(r)] = pickle.dumps(r, 2)
        return rlist
    
    def packageFailure(self, f):
        f.cleanFailure()
        pString = pickle.dumps(f, 2)
        return 'FAILURE:' + pString
    
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_execute(self, request, targets, lines):
        d = self.multiEngine.execute(targets, lines)
        return d.addErrback(self.packageFailure)
    
    def xmlrpc_push(self, request, targets, pNamespace):
        try:
            namespace = pickle.loads(pNamespace)
        except:
            return defer.fail(self.packageFailure(failure.Failure()))
        else:
            return blockOn(self.multiEngine.push(targets, **namespace).addErrback(self.packageFailure))
    
    def xmlrpc_pull(self, request, targets, *keys):
        d = self.multiEngine.pull(targets, *keys)
        d.addCallback(pickle.dumps, 2)
        d.addErrback(self.packageFailure)
        return blockOn(d)
    
    def xmlrpc_getResult(self, request, targets, i=None):
        return self.multiEngine.getResult(targets, i).addErrback(self.packageFailure)
    
    def xmlrpc_reset(self, request, targets):
        return self.multiEngine.reset(targets).addErrback(self.packageFailure)
    
    def xmlrpc_keys(self, request, targets):
        return self.multiEngine.keys(targets).addErrback(self.packageFailure)
    
    def xmlrpc_kill(self, request, targets, controller=False):
        return self.multiEngine.kill(targets, controller).addErrback(self.packageFailure)
        
    def xmlrpc_pushSerialized(self, request, targets, pNamespace):
        try:
            namespace = pickle.loads(pNamespace)
        except:
            return defer.fail(failure.Failure()).addErrback(self.packageFailure)
        else:
            d = self.multiEngine.pushSerialized(targets, **namespace)
            return d.addErrback(self.packageFailure)
    
    def xmlrpc_pullSerialized(self, request, targets, *keys):
        d = self.multiEngine.pullSerialized(targets, *keys)
        d.addCallback(pickle.dumps, 2)
        d.addErrback(self.packageFailure)
        return d
    
    def xmlrpc_clearQueue(self, request, targets):
        return self.multiEngine.clearQueue(targets).addErrback(self.packageFailure)
    
    def xmlrpc_queueStatus(self, request, targets):
        return self.multiEngine.queueStatus(targets).addErrback(self.packageFailure)
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_getIDs(self, request):
        return self.multiEngine.getIDs().addErrback(self.packageFailure)
    
    def xmlrpc_verifyTargets(self, request, targets):
        return self.multiEngine.verifyTargets(targets).addErrback(self.packageFailure)
    
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_scatter(self, request, targets, key, pseq, style='basic', flatten=False):
        try:
            seq = pickle.loads(pseq)
        except:
            return defer.fail(failure.Failure()).addErrback(self.packageFailure)
        else:
            d = self.multiEngine.scatter(targets, key, seq, style, flatten)
            return d.addErrback(self.packageFailure)
    
    def xmlrpc_gather(self, request, targets, key, style='basic'):
        d = self.multiEngine.gather(targets, key, style)
        d.addCallback(pickle.dumps, 2)
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
        
    def checkReturnForFailure(self, r):
        """See if a returned value is a pickled Failure object.
        
        To distinguish between general pickled objects and pickled Failures, the
        other side should prepend the string FAILURE: to any pickled Failure.
        """
        if isinstance(r, str):
            if r.startswith('FAILURE:'):
                try: 
                    result = pickle.loads(r[8:])
                except pickle.PickleError:
                    return failure.Failure( \
                        FailureUnpickleable("Could not unpickle failure."))
                else:
                    return result
        return r
        
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
        
    def execute(self, targets, lines):
        return self.checkReturnForFailure(self.server.execute(targets, lines))
    
    def executeAll(self, lines):
        return self.execute('all', lines)
    
    def push(self, targets, **namespace):
        try:
            package = pickle.dumps(namespace, 2)
        except:
            return failure.Failure()
        else:
            return self.checkReturnForFailure(self.server.push(targets, package))
    
    def pushAll(self, **ns):
        return self.push('all', **ns)
    
    def pull(self, targets, *keys):
        r = self.checkReturnForFailure(self.server.pull(targets, *keys))
        if not isinstance(r, failure.Failure):
            return pickle.loads(r)
        return r
    
    def pullAll(self, *keys):
        return self.pull('all', *keys)
        
    def getResult(self, targets, i=None):
        return self.checkReturnForFailure(self.server.getResult(targets, i))
    
    def getResultAll(self, i=None):
        return self.getResult('all', i)
    
    def reset(self, targets):
        return self.checkReturnForFailure(self.server.reset(targets))
    
    def resetAll(self):
        return self.reset('all')
    
    def keys(self, targets):
        return self.checkReturnForFailure(self.server.keys(targets))
    
    def keysAll(self):
        return self.keys('all')
    
    def kill(self, targets, controller=False):
        return self.checkReturnForFailure(self.server.kill(targets, controller))
    
    def killAll(self, controller=False):
        return self.kill('all', controller)
    
    def pushSerialized(self, targets, **namespace):
        try:
            package = pickle.dumps(namespace, 2)
        except:
            return failure.Failure()
        else:
            return self.checkReturnForFailure(self.server.pushSerialized(targets, package))
    
    def pushSerializedAll(self, **namespace):
        return self.pushSerialized('all', **namespace)
    
    def pullSerialized(self, targets, *keys):
        r = self.checkReturnForFailure(self.server.pullSerialized(targets, *keys))
        if not isinstance(r, failure.Failure):
            return pickle.loads(r)
        return r
    
    def pullSerializedAll(self, *keys):
        return self.pullSerialized('all', *keys)
    
    def clearQueue(self, targets):
        return self.checkReturnForFailure(self.server.clearQueue(targets))
    
    def clearQueueAll(self):
        return self.clearQueue('all')
    
    def queueStatus(self, targets):
        return self.checkReturnForFailure(self.server.queueStatus(targets))
    
    def queueStatusAll(self):
        return self.queueStatus('all')
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def getIDs(self):
        return self.checkReturnForFailure(self.server.getIDs())
    
    def verifyTargets(self, targets):
        return self.checkReturnForFailure(self.server.verifyTargets(targets))
    
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
    
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        try:
            pseq = pickle.dumps(seq, 2)
        except:
            return failure.Failure()
        else:
            return self.checkReturnForFailure(self.server.scatter(targets, key, pseq, style, flatten))
    
    def gather(self, targets, key, style='basic'):
        r = self.checkReturnForFailure(self.server.gather(targets, key, style='basic'))
        if not isinstance(r, failure.Failure):
            return pickle.loads(r)
        return r
    

components.registerAdapter(XMLRPCMultiEngineClient, 
        xmlrpclib.Server, IMultiEngine)
    
    
#-------------------------------------------------------------------------------
# The XMLRPC version of RemoteController
#-------------------------------------------------------------------------------

class RemoteController(object):
    """A high-level XMLRPCRemoteController."""
    
    def __init__(self, addr):
        """addr is a string address"""
        self.addr = addr
        self.multiengine = None
        self.pendingDeferreds = []
        self.connected = False
    
    def connect(self):
        if not self.connected:
            print "Connecting to ", self.addr
            self.multiengine = XMLRPCMultiEngineClient(xmlrpclib.Server(self.addr))
            self.connected = True
    
    def disconnect(self):
        self.factory.disconnect()
        for i in range(10):
            reactor.iterate(0.1)
    
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
        return self.multiengine.execute(targets, lines)
    
    def executeAll(self, lines):
        return self.execute('all', lines)
    
    def push(self, targets, **namespace):
        self.connect()
        return self.multiengine.push(targets, **namespace)
    
    def pushAll(self, **namespace):
        return self.push('all', **namespace)
    
    def pull(self, targets, *keys):
        self.connect()
        return self.multiengine.pull(targets, *keys)
    
    def pullAll(self, *keys):
        return self.pull('all', *keys)
    
    def getResult(self, targets, i=None):
        self.connect()
        return self.multiengine.getResult(targets, i)
    
    def getResultAll(self, i=None):
        return self.getResult('all', i)
    
    def reset(self, targets):
        self.connect()
        return self.multiengine.reset(targets)
    
    def resetAll(self):
        return self.reset('all')
    
    def keys(self, targets):
        self.connect()
        return self.multiengine.keys(targets)
    
    def keysAll(self):
        return self.keys('all')
    
    def kill(self, targets, controller=False):
        self.connect()
        return self.multiengine.kill(targets, controller)
    
    def killAll(self, controller=False):
        return self.kill('all', controller)
    
    def pushSerialized(self, targets, **namespace):
        self.connect()
        return self.multiengine.pushSerialized(targets, **namespace)
    
    def pushSerializedAll(self, **namespace):
        return self.pushSerialized('all', **namespace)
    
    def pullSerialized(self, targets, *keys):
        self.connect()
        return self.multiengine.pullSerialized(targets, *keys)
    
    def pullSerializedAll(self, *keys):
        return self.pullSerialized('all', *keys)
    
    def clearQueue(self, targets):
        self.connect()
        return self.multiengine.clearQueue(targets)
    
    def clearQueueAll(self):
        return self.clearQueue('all')
    
    def queueStatus(self, targets):
        self.connect()
        return self.multiengine.queueStatus(targets)
    
    def queueStatusAll(self):
        return self.queueStatus('all')
    
    def getIDs(self):
        self.connect()
        return self.multiengine.getIDs()
    
    def verifyTargets(self, targets):
        self.connect()
        return self.multiengine.verifyTargets(targets)
    
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        self.connect()
        return self.multiengine.scatter(targets, key, seq, style, flatten)
    
    def gather(self, targets, key, style='basic'):
        self.connect()
        return self.multiengine.gather(targets, key, style)
    
