# encoding: utf-8
# -*- test-case-name: ipython1.test.test_multienginepb -*-
"""A Perspective Broker interface to a MultiEngine.

This class lets PB clients talk to the ControllerService.  The main difficulty
is that PB doesn't allow arbitrary objects to be sent over the wire - only
basic Python types.  To get around this we simple pickle more complex objects
on boths side of the wire.  That is the main thing these classes have to 
manage.

Todo:
* Determine methods that won't use 2 phase submit/retrieve
  - getIDs
  - verfiyTargets
  - queueStatus?
* Scatter/gather has a problem

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

from twisted.internet import reactor, defer
from twisted.python import components, log
from twisted.python.failure import Failure
from twisted.python import failure
from twisted.spread import pb
from zope.interface import Interface, implements

from ipython1.kernel import pbconfig
from ipython1.kernel.pbutil import packageFailure, checkMessageSize
from ipython1.kernel.multiengine import MultiEngine, IMultiEngine
from ipython1.kernel.blockon import blockOn
from ipython1.kernel.error import PBMessageSizeError
from ipython1.kernel import error
from ipython1.kernel.multiengineclient import InteractiveMultiEngineClient, \
    IBlockingMultiEngine


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
        self.deferredID = 0
        self.pendingDeferreds = {}

    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------

    def _getNextDeferredID(self):
        did = self.deferredID
        self.deferredID += 1
        return did
        
    def remote_getPendingDeferred(self, deferredID):
        pd = self.pendingDeferreds.get(deferredID)
        # Delete the pd after it is requested.
        # 
        if pd is not None:
            if not pd.called:
                log.msg("pendingDeferred has not been called: %s" % deferredID)
                d = defer.Deferred()
                pd.chainDeferred(d)
                return d.addErrback(packageFailure)
            else:
                log.msg("pendingDeferred has been called: %s: %s" % (deferredID, repr(pd.result)))
                if isinstance(pd.result, failure.Failure):
                    return defer.fail(pd.result).addErrback(packageFailure)
                else:
                    return defer.succeed(pd.result)
        else:
            return defer.fail(failure.Failure(Exception('Invalid deferredID'))).addErrback(packageFailure)
        
    def checkReturns(self, rlist):
        for r in rlist:
            if isinstance(r, (Failure, Exception)):
                rlist[rlist.index(r)] = pickle.dumps(r, 2)
        return rlist
        
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------

    def remote_execute(self, targets, lines):
        if not self.multiEngine.verifyTargets(targets):
            return defer.fail(error.InvalidEngineID(repr(targets)))
        else:
            deferredID = self._getNextDeferredID()
            d = self.multiEngine.execute(targets, lines)
            self.pendingDeferreds[deferredID] = d
            return defer.succeed(deferredID)
            
    def remote_push(self, targets, pNamespace):
        if not self.multiEngine.verifyTargets(targets):
            return defer.fail(error.InvalidEngineID(repr(targets)))
        else:
            try:
                namespace = pickle.loads(pNamespace)
            except:
                return defer.fail(failure.Failure()).addErrback(packageFailure)
            else:
                deferredID = self._getNextDeferredID()
                d = self.multiEngine.push(targets, **namespace)
                self.pendingDeferreds[deferredID] = d
                return defer.succeed(deferredID)
    
    def remote_pull(self, targets, *keys):
        if not self.multiEngine.verifyTargets(targets):
            return defer.fail(error.InvalidEngineID(repr(targets)))
        else:
            deferredID = self._getNextDeferredID()
            d = self.multiEngine.pull(targets, *keys)
            d.addCallback(pickle.dumps, 2)
            d.addCallback(checkMessageSize, repr(keys))
            self.pendingDeferreds[deferredID] = d
            return defer.succeed(deferredID)
    
    def remote_getResult(self, targets, i=None):
        if not self.multiEngine.verifyTargets(targets):
            return defer.fail(error.InvalidEngineID(repr(targets)))
        else:
            deferredID = self._getNextDeferredID()
            d = self.multiEngine.getResult(targets, i)
            self.pendingDeferreds[deferredID] = d
            return defer.succeed(deferredID)

    def remote_reset(self, targets):
        if not self.multiEngine.verifyTargets(targets):
            return defer.fail(error.InvalidEngineID(repr(targets)))
        else:
            deferredID = self._getNextDeferredID()
            d = self.multiEngine.reset(targets)
            self.pendingDeferreds[deferredID] = d
            return defer.succeed(deferredID)
    
    def remote_keys(self, targets):
        if not self.multiEngine.verifyTargets(targets):
            return defer.fail(error.InvalidEngineID(repr(targets)))
        else:
            deferredID = self._getNextDeferredID()
            d = self.multiEngine.keys(targets)
            self.pendingDeferreds[deferredID] = d
            return defer.succeed(deferredID)
    
    def remote_kill(self, targets, controller=False):
        if not self.multiEngine.verifyTargets(targets):
            return defer.fail(error.InvalidEngineID(repr(targets)))
        else:
            deferredID = self._getNextDeferredID()
            d = self.multiEngine.kill(targets, controller)
            self.pendingDeferreds[deferredID] = d
            return defer.succeed(deferredID)
        
    def remote_pushSerialized(self, targets, pNamespace):
        if not self.multiEngine.verifyTargets(targets):
            return defer.fail(error.InvalidEngineID(repr(targets)))
        else:
            try:
                namespace = pickle.loads(pNamespace)
            except:
                return defer.fail(failure.Failure()).addErrback(packageFailure)
            else:
                deferredID = self._getNextDeferredID()
                d = self.multiEngine.pushSerialized(targets, **namespace)
                self.pendingDeferreds[deferredID] = d
                return defer.succeed(deferredID)
    
    def remote_pullSerialized(self, targets, *keys):
        if not self.multiEngine.verifyTargets(targets):
            return defer.fail(error.InvalidEngineID(repr(targets)))
        else:
            deferredID = self._getNextDeferredID()
            d = self.multiEngine.pullSerialized(targets, *keys)
            d.addCallback(pickle.dumps, 2)
            d.addCallback(checkMessageSize, repr(keys))
            self.pendingDeferreds[deferredID] = d
            return defer.succeed(deferredID)
    
    def remote_clearQueue(self, targets):
        if not self.multiEngine.verifyTargets(targets):
            return defer.fail(error.InvalidEngineID(repr(targets)))
        else:
            deferredID = self._getNextDeferredID()
            d = self.multiEngine.clearQueue(targets)
            self.pendingDeferreds[deferredID] = d
            return defer.succeed(deferredID)
    
    def remote_queueStatus(self, targets):
        if not self.multiEngine.verifyTargets(targets):
            return defer.fail(error.InvalidEngineID(repr(targets)))
        else:
            deferredID = self._getNextDeferredID()
            d = self.multiEngine.queueStatus(targets)
            self.pendingDeferreds[deferredID] = d
            return defer.succeed(deferredID)

    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------

    def remote_getIDs(self):
        d = self.multiEngine.getIDs()
        d.addErrback(packageFailure)
        return d
    
    def remote_verifyTargets(self, targets):
        result = self.multiEngine.verifyTargets(targets)
        return defer.succeed(result)
    
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
    
    def remote_scatter(self, targets, key, pseq, style, flatten):
        if not self.multiEngine.verifyTargets(targets):
            return defer.fail(error.InvalidEngineID(repr(targets)))
        else:
            try:
                seq = pickle.loads(pseq)
            except:
                return defer.fail(failure.Failure()).addErrback(packageFailure)
            else:
                deferredID = self._getNextDeferredID()
                d = self.multiEngine.scatter(targets, key, seq, style, flatten)
                self.pendingDeferreds[deferredID] = d
                return defer.succeed(deferredID)
    
    def remote_gather(self, targets, key, style):
        if not self.multiEngine.verifyTargets(targets):
            return defer.fail(error.InvalidEngineID(repr(targets)))
        else:
            deferredID = self._getNextDeferredID()
            d = self.multiEngine.gather(targets, key, style)
            d.addCallback(pickle.dumps, 2)
            d.addCallback(checkMessageSize, repr(key))
            self.pendingDeferreds[deferredID] = d
            return defer.succeed(deferredID)
    

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
    
    implements(IBlockingMultiEngine)
    
    def __init__(self, reference):
        self.reference = reference
        self.callRemote = reference.callRemote
        self.block = True
        
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

    def _getPendingDeferred(self, deferredID):
        d = self.callRemote('getPendingDeferred', deferredID)
        return d.addCallback(self.checkReturnForFailure)
                      
    def _getActualDeferred(self, d):    
        deferredID = self.blockOn(d)
        print "Submitted action, got deferredID: ", deferredID
        d2 = self._getPendingDeferred(deferredID)
        return d2
                      
    def _blockOrNot(self, d):
        if self.block:
            return self.blockOn(d)
        else:
            return d
           
    def blockOn(self, d):
        return blockOn(d)  

    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
        
    def execute(self, targets, lines, block=None):
        d = self.callRemote('execute', targets, lines)
        d.addCallback(self.checkReturnForFailure)
        d2 = self._getActualDeferred(d)
        if (self.block and block is None) or block:
            return self.blockOn(d2)
        else:
            return d2

    def executeAll(self, lines):
        return self.execute('all', lines)
    
    def push(self, targets, **namespace):
        try:
            package = pickle.dumps(namespace, 2)
        except:
            return defer.fail(failure.Failure())
        else:
            package = checkMessageSize(package, namespace.keys())
            if isinstance(package, failure.Failure):
                return defer.fail(package)
            else:
                d = self.callRemote('push', targets, package)
                d.addCallback(self.checkReturnForFailure)
                d2 = self._getActualDeferred(d)
                return self._blockOrNot(d2)
                    
    def pushAll(self, **ns):
        return self.push('all', **ns)
    
    def pull(self, targets, *keys):
        d = self.callRemote('pull', targets, *keys)
        d.addCallback(self.checkReturnForFailure)
        d2 = self._getActualDeferred(d)
        d2.addCallback(pickle.loads)
        return self._blockOrNot(d2)

    def pullAll(self, *keys):
        return self.pull('all', *keys)
        
    def getResult(self, targets, i=None):
        d = self.callRemote('getResult', targets, i)
        d.addCallback(self.checkReturnForFailure)
        d2 = self._getActualDeferred(d)
        return self._blockOrNot(d2)
    
    def getResultAll(self, i=None):
        return self.getResult('all', i)
    
    def reset(self, targets):
        d = self.callRemote('reset', targets)
        d.addCallback(self.checkReturnForFailure)
        d2 = self._getActualDeferred(d)
        return self._blockOrNot(d2)
        
    def resetAll(self):
        return self.reset('all')
    
    def keys(self, targets):
        d = self.callRemote('keys', targets)
        d.addCallback(self.checkReturnForFailure)
        d2 = self._getActualDeferred(d)
        return self._blockOrNot(d2)
        
    def keysAll(self):
        return self.keys('all')
    
    def kill(self, targets, controller=False):
        d = self.callRemote('kill', targets, controller)
        d.addCallback(self.checkReturnForFailure)
        try:
            deferredID = self.blockOn(d)
        except pb.PBConnectionLost:
            pass
        else:
            print "Submitted action, got deferredID: ", deferredID
            d2 = self._getPendingDeferred(deferredID)
            d2.addErrback(self.killBack)
            return d2
        
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
            package = checkMessageSize(package, namespace.keys())
            if isinstance(package, failure.Failure):
                return defer.fail(package)
            else:
                d = self.callRemote('pushSerialized', targets, package)
                d.addCallback(self.checkReturnForFailure)
                d2 = self._getActualDeferred(d)
                return self._blockOrNot(d2)
    
    def pushSerializedAll(self, **namespace):
        return self.pushSerialized('all', **namespace)
    
    def pullSerialized(self, targets, *keys):
        d = self.callRemote('pullSerialized', targets, *keys)
        d.addCallback(self.checkReturnForFailure)
        d2 = self._getActualDeferred(d)
        d2.addCallback(pickle.loads)
        return self._blockOrNot(d2)
    
    def pullSerializedAll(self, *keys):
        return self.pullSerialized('all', *keys)
    
    def clearQueue(self, targets):
        d = self.callRemote('clearQueue', targets)
        d.addCallback(self.checkReturnForFailure)
        d2 = self._getActualDeferred(d)
        return self._blockOrNot(d2)
        
    def clearQueueAll(self):
        return self.clearQueue('all')
    
    def queueStatus(self, targets):
        d = self.callRemote('queueStatus', targets)
        d.addCallback(self.checkReturnForFailure)
        d2 = self._getActualDeferred(d)
        return self._blockOrNot(d2)
            
    def queueStatusAll(self):
        return self.queueStatus('all')
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def getIDs(self):
        d = self.callRemote('getIDs')
        d.addCallback(self.checkReturnForFailure)
        return self.blockOn(d)
        
    def verifyTargets(self, targets):
        d = self.callRemote('verifyTargets', targets)
        d.addCallback(self.checkReturnForFailure)
        return self.blockOn(d)
            
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
    
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        try:
            pseq = pickle.dumps(seq, 2)
        except:
            return defer.fail(failure.Failure())
        else:
            pseq = checkMessageSize(pseq, key)
            if isinstance(pseq, failure.Failure):
                return defer.fail(pseq)
            else:
                d = self.callRemote('scatter', targets=targets, key=key, 
                                    pseq=pseq, style=style, flatten=flatten)
                d.addCallback(self.checkReturnForFailure)
                d2 = self._getActualDeferred(d)
                return self._blockOrNot(d2)

    def gather(self, targets, key, style='basic'):
        d = self.callRemote('gather', targets=targets, key=key, style=style)
        d.addCallback(self.checkReturnForFailure)
        d2 = self._getActualDeferred(d)
        d2.addCallback(pickle.loads)
        return self._blockOrNot(d2)
    

components.registerAdapter(PBMultiEngineClient, 
        pb.RemoteReference, IMultiEngine)


class PBInteractiveMultiEngineClient(InteractiveMultiEngineClient):
    
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
        self.multiengine = None
        self.factory = None
            
    def _gotRoot(self, rootObj):
        self.multiengine = IMultiEngine(rootObj)
        self.multiengine.block = self._block
        self.connected = True
        self.multiengine.reference.notifyOnDisconnect(self.handleDisconnect)
        


