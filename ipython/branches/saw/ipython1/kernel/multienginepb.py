# encoding: utf-8
# -*- test-case-name: ipython1.test.test_multienginepb -*-
"""A Perspective Broker interface to a MultiEngine.

This class lets PB clients talk to the ControllerService.  The main difficulty
is that PB doesn't allow arbitrary objects to be sent over the wire - only
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

from twisted.internet import reactor
from twisted.python import components
from twisted.python.failure import Failure
from twisted.spread import pb
from zope.interface import Interface, implements

import ipython1.kernel.pbconfig
from ipython1.kernel.multiengine import MultiEngine, IMultiEngine
from ipython1.kernel.blockon import blockOn
from ipython1.kernel.util import gatherBoth


#-------------------------------------------------------------------------------
# The Controller side of things
#-------------------------------------------------------------------------------

class IPBMultiEngine(Interface):
    """Perspective Broker interface to controller.  

    The methods in this interface are similar to those from IEngineMultiplexer, 
    but their arguments and return values are pickled if they are not already
    simple Python types so they can be send over PB.  This is to deal with 
    the fact that w/o a lot of work PB cannot send arbitrary objects over the
    wire.

    See the documentation of IEngineMultiplexer for documentation about the methods.
    """
            
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
            
    def remote_execute(targets, lines):
        """"""
        
    def remote_push(targets, **namespace):
        """"""
        
    def remote_pull(targets, *keys):
        """"""
        
    def remote_getResult(targets, i=None):
        """"""
        
    def remote_reset(targets):
        """"""
        
    def remote_keys(targets):
        """"""
        
    def remote_kill(targets, controller=False):
        """"""
        
    def remote_pushSerialized(targets, **namespace):
        """"""
        
    def remote_pullSerialized(targets, *keys):
        """"""
        
    def remote_clearQueue(targets):
        """"""
        
    def remote_queueStatus(targets):
        """"""
        
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
        
    def remote_getIDs():
        """"""
        
    def remote_verifyTargets(targets):
        """"""
    
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
        
    def remote_scatter(targets, key, seq, style='basic', flatten=False):
        """"""
        
    def remote_gather(targets, key, style='basic'):
        """"""
                
        
class PBMultiEngineFromMultiEngine(pb.Root):
    """Perspective Broker interface to controller.
    
    See IPBMultiEngine and IMultiEngine (and its children) for documentation. 
    """
    
    implements(IPBMultiEngine)
    
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
    
    def remote_execute(self, targets, lines):
        d = self.multiEngine.execute(targets, lines)
        return d.addErrback(self.packageFailure)
    
    def remote_push(self, targets, pNamespace):
        try:
            namespace = pickle.loads(pNamespace)
        except:
            return defer.fail(failure.Failure()).addErrback(self.packageFailure)
        else:
            return self.multiEngine.push(targets, **namespace).addErrback(self.packageFailure)
    
    def remote_pull(self, targets, *keys):
        d = self.multiEngine.pull(targets, *keys)
        d.addCallback(pickle.dumps, 2)
        d.addErrback(self.packageFailure)
        return d
    
    def remote_getResult(self, targets, i=None):
        return self.multiEngine.getResult(targets, i).addErrback(self.packageFailure)
    
    def remote_reset(self, targets):
        return self.multiEngine.reset(targets).addErrback(self.packageFailure)
    
    def remote_keys(self, targets):
        return self.multiEngine.keys(targets).addErrback(self.packageFailure)
    
    def remote_kill(self, targets, controller=False):
        return self.multiEngine.kill(targets, controller).addErrback(self.packageFailure)
        
    def remote_pushSerialized(self, targets, pNamespace):
        try:
            namespace = pickle.loads(pNamespace)
        except:
            return defer.fail(failure.Failure()).addErrback(self.packageFailure)
        else:
            d = self.multiEngine.pushSerialized(targets, **namespace)
            return d.addErrback(self.packageFailure)
    
    def remote_pullSerialized(self, targets, *keys):
        d = self.multiEngine.pullSerialized(targets, *keys)
        d.addCallback(pickle.dumps, 2)
        d.addErrback(self.packageFailure)
        return d
    
    def remote_clearQueue(self, targets):
        return self.multiEngine.clearQueue(targets).addErrback(self.packageFailure)
    
    def remote_queueStatus(self, targets):
        return self.multiEngine.queueStatus(targets).addErrback(self.packageFailure)

    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------

    def remote_getIDs(self):
        return self.multiEngine.getIDs().addErrback(self.packageFailure)
    
    def remote_verifyTargets(self, targets):
        return self.multiEngine.verifyTargets(targets).addErrback(self.packageFailure)
    
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
    
    def remote_scatter(self, targets, key, pseq, style='basic', flatten=False):
        try:
            seq = pickle.loads(pseq)
        except:
            return defer.fail(failure.Failure()).addErrback(self.packageFailure)
        else:
            d = self.multiEngine.scatter(targets, key, seq, style, flatten)
            return d.addErrback(self.packageFailure)
    
    def remote_gather(self, targets, key, style='basic'):
        d = self.multiEngine.gather(targets, key, style)
        d.addCallback(pickle.dumps, 2)
        d.addErrback(self.packageFailure)
        return d
    

components.registerAdapter(PBMultiEngineFromMultiEngine,
            MultiEngine, IPBMultiEngine)


class IPBMultiEngineFactory(Interface):
    pass
    
    
def PBServerFactoryFromMultiEngine(multiEngine):
    """Adapt a MultiEngine to a PBServerFactory."""
    
    return pb.PBServerFactory(IPBMultiEngine(multiEngine))
    
    
components.registerAdapter(PBServerFactoryFromMultiEngine,
            MultiEngine, IPBMultiEngineFactory)
        

#-------------------------------------------------------------------------------
# The Client side of things
#-------------------------------------------------------------------------------

class PBMultiEngineClient(object):
    """PB based MultiEngine client that implements IMultiEngine.
    
    One could have this inherit from pb.Referencable and implement remote_foo
    methods to allow the MultiEngine to call methods on this class.  This is
    how the old notification system worked.
    """
    
    implements(IMultiEngine)
    
    def __init__(self, reference):
        self.reference = reference
        self.callRemote = reference.callRemote
        
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
        d = self.callRemote('execute', targets, lines)
        return d.addCallback(self.checkReturnForFailure)
    
    def executeAll(self, lines):
        return self.execute('all', lines)
    
    def push(self, targets, **namespace):
        try:
            package = pickle.dumps(namespace, 2)
        except:
            return defer.fail(failure.Failure())
        else:
            d = self.callRemote('push', targets, package)
            return d.addCallback(self.checkReturnForFailure)
    
    def pushAll(self, **ns):
        return self.push('all', **ns)
    
    def pull(self, targets, *keys):
        d = self.callRemote('pull', targets, *keys)
        d.addCallback(self.checkReturnForFailure)
        d.addCallback(pickle.loads)
        return d
    
    def pullAll(self, *keys):
        return self.pull('all', *keys)
        
    def getResult(self, targets, i=None):
        return self.callRemote('getResult', targets, i).addCallback(self.checkReturnForFailure)
    
    def getResultAll(self, i=None):
        return self.getResult('all', i)
    
    def reset(self, targets):
        return self.callRemote('reset', targets).addCallback(self.checkReturnForFailure)
    
    def resetAll(self):
        return self.reset('all')
    
    def keys(self, targets):
        return self.callRemote('keys', targets).addCallback(self.checkReturnForFailure)
    
    def keysAll(self):
        return self.keys('all')
    
    def kill(self, targets, controller=False):
        d = self.callRemote('kill', targets, controller)
        d.addCallback(self.checkReturnForFailure)
        d.addErrback(self.killBack)
        return d
    
    def killBack(self, f):
        f.trap(pb.PBConnectionLost)
        return None
    
    def killAll(self, controller=False):
        return self.kill('all', controller)
    
    def pushSerialized(self, targets, **namespace):
        try:
            package = pickle.dumps(namespace, 2)
        except:
            return defer.fail(failure.Failure())
        else:
            d = self.callRemote('pushSerialized', targets, package)
            return d.addCallback(self.checkReturnForFailure)
    
    def pushSerializedAll(self, **namespace):
        return self.pushSerialized('all', **namespace)
    
    def pullSerialized(self, targets, *keys):
        d = self.callRemote('pullSerialized', targets, *keys)
        d.addCallback(self.checkReturnForFailure)
        d.addCallback(pickle.loads)
        return d
    
    def pullSerializedAll(self, *keys):
        return self.pullSerialized('all', *keys)
    
    def clearQueue(self, targets):
        d = self.callRemote('clearQueue', targets)
        return d.addCallback(self.checkReturnForFailure)
    
    def clearQueueAll(self):
        return self.clearQueue('all')
    
    def queueStatus(self, targets):
        d = self.callRemote('queueStatus', targets)
        return d.addCallback(self.checkReturnForFailure)
    
    def queueStatusAll(self):
        return self.queueStatus('all')
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def getIDs(self):
        d = self.callRemote('getIDs')
        return d.addCallback(self.checkReturnForFailure)
    
    def verifyTargets(self, targets):
        d = self.callRemote('verifyTargets', targets)
        return d.addCallback(self.checkReturnForFailure)
    
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
    
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        try:
            pseq = pickle.dumps(seq, 2)
        except:
            return defer.fail(failure.Failure())
        else:
            d = self.callRemote('scatter', targets, key, pseq, style, flatten)
            return d.addCallback(self.checkReturnForFailure)
    
    def gather(self, targets, key, style='basic'):
        d = self.callRemote('gather', targets, key, style='basic')
        d.addCallback(self.checkReturnForFailure)
        d.addCallback(pickle.loads)
        return d
    

components.registerAdapter(PBMultiEngineClient, 
        pb.RemoteReference, IMultiEngine)
    
    
#-------------------------------------------------------------------------------
# The PB version of RemoteController
#-------------------------------------------------------------------------------

class RemoteController(object):
    """A synchronous high-level PBRemoteController."""
    
    def __init__(self, addr):
        self.addr = addr
        self.pbClient = None
        self.factory = None
        self.pendingDeferreds = []
        self.connected = False
        
    def connect(self):
        if not self.connected:
            print "Connecting to ", self.addr
            self.factory = pb.PBClientFactory()
            d = self.factory.getRootObject()
            d.addCallback(self._gotRoot)
            reactor.connectTCP(self.addr[0], self.addr[1], self.factory)
            return blockOn(d)

    def disconnect(self):
        self.factory.disconnect()
        for i in range(10):
            reactor.iterate(0.1)
            
    def handleDisconnect(self, thingy):
        print "Disconnecting from ", self.addr
        self.connected = False
        self.pbClient = None
        self.factory = None
            
    def _gotRoot(self, rootObj):
        self.pbClient = IMultiEngine(rootObj)
        self.connected = True
        self.pbClient.reference.notifyOnDisconnect(self.handleDisconnect)

    def block(self, fireOnOneCallback=0, fireOnOneErrback=0, consumeErrors=0):
        totalD = gatherBoth(self.pendingDeferreds,
                       fireOnOneCallback, 
                       fireOnOneErrback,
                       consumeErrors,
                       logErrors=0)
        def removeFromPendingDeferreds(r, d):
            self.pendingDeferreds.remove(d)
            return r
        for d in self.pendingDeferreds:
            d.addBoth(removeFromPendingDeferreds, d)
        return blockOn(totalD)
                
    #---------------------------------------------------------------------------
    # Interface methods
    #---------------------------------------------------------------------------

    def execute(self, targets, lines):
        self.connect()
        d = self.pbClient.execute(targets, lines)
        self.pendingDeferreds.append(d)
        return d
        
    def executeAll(self, lines):
        return self.execute('all', lines)
        
    def push(self, targets, **namespace):
        self.connect()
        d = self.pbClient.push(targets, **namespace)
        self.pendingDeferreds.append(d)
        return d
        
    def pushAll(self, **namespace):
        return self.push('all', **namespace)
        
    def pull(self, targets, *keys):
        self.connect()
        d = self.pbClient.pull(targets, *keys)
        self.pendingDeferreds.append(d)
        return d
    
    def pullAll(self, *keys):
        return self.pull('all', *keys)
    
    def getResult(self, targets, i=None):
        self.connect()
        d = self.pbClient.getResult(targets, i)
        self.pendingDeferreds.append(d)
        return d       
    
    def getResultAll(self, i=None):
        return self.getResult('all', i)
    
    def reset(self, targets):
        self.connect()
        d = self.pbClient.reset(targets)
        self.pendingDeferreds.append(d)
        return d
    
    def resetAll(self):
        return self.reset('all')
    
    def keys(self, targets):
        self.connect()
        d = self.pbClient.keys(targets)
        self.pendingDeferreds.append(d)
        return d
    
    def keysAll(self):
        return self.keys('all')
    
    def kill(self, targets, controller=False):
        self.connect()
        d = self.pbClient.kill(targets, controller)
        self.pendingDeferreds.append(d)
        return d
        
    def killAll(self, controller=False):
        return self.kill('all', controller)
    
    def pushSerialized(self, targets, **namespace):
        self.connect()
        d = self.pbClient.pushSerialized(targets, **namespace)
        self.pendingDeferreds.append(d)
        return d
    
    def pushSerializedAll(self, **namespace):
        return self.pushSerialized('all', **namespace)
    
    def pullSerialized(self, targets, *keys):
        self.connect()
        d = self.pbClient.pullSerialized(targets, *keys)
        self.pendingDeferreds.append(d)
        return d
    
    def pullSerializedAll(self, *keys):
        return self.pullSerialized('all', *keys)
    
    def clearQueue(self, targets):
        self.connect()
        d = self.pbClient.clearQueue(targets)
        self.pendingDeferreds.append(d)
        return d
    
    def clearQueueAll(self):
        return self.clearQueue('all')
    
    def queueStatus(self, targets):
        self.connect()
        d = self.pbClient.queueStatus(targets)
        self.pendingDeferreds.append(d)
        return d
    
    def queueStatusAll(self):
        return self.queueStatus('all')
        
    def getIDs(self):
        self.connect()
        d = self.pbClient.getIDs()
        self.pendingDeferreds.append(d)
        return d
    
    def verifyTargets(self, targets):
        self.connect()
        d = self.pbClient.verifyTargets(targets)
        self.pendingDeferreds.append(d)
        return d
        
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        self.connect()
        d = self.pbClient.scatter(targets, key, seq, style, flatten)
        self.pendingDeferreds.append(d)
        return d
    
    def gather(self, targets, key, style='basic'):
        self.connect()
        d = self.pbClient.gather(targets, key, style)
        self.pendingDeferreds.append(d)
        return d