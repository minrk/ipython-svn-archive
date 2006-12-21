# encoding: utf-8
# -*- test-case-name: ipython1.test.test_controllerpb -*-
"""A Perspective Broker interface to a MultiEngine.

This class lets PB clients talk to the ControllerService.  The main difficulty
is that PB doesn't allow arbitrary objects to be sent over the wire - only
basic Python types.  To get around this we simple pickle more complex objects
on boths side of the wire.  That is the main thing these classes have to 
manage.

To do:

 * remote_addNotifier is not in the ControllerService implem. or interf.
 * PBNotifierChild need documentation.
 * How are objects moving through PB?
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

from ipython1.kernel.multiengine import MultiEngine, IMultiEngine
from ipython1.kernel.blockon import blockOn


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
        
    def remote_pullNamespace(targets, *keys):
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
    
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
    
    def remote_execute(self, targets, lines):
        d = self.multiEngine.execute(targets, lines)
        return d.addErrback(pickle.dumps, 2)
    
    def remote_push(self, targets, pns):
        d = self.multiEngine.push(targets, **pickle.loads(pns))
        return d.addErrback(pickle.dumps, 2)
    
    def remote_pull(self, targets, *keys):
        return self.multiEngine.pull(targets, *keys).addBoth(pickle.dumps, 2)
    
    def remote_pullNamespace(self, targets, *keys):
        d = self.multiEngine.pullNamespace(targets, *keys)
        return d.addBoth(pickle.dumps, 2)
    
    def remote_getResult(self, targets, i=None):
        d = self.multiEngine.getResult(targets, i).addCallback(self.checkReturns)
        return d.addErrback(pickle.dumps, 2)
    
    def remote_reset(self, targets):
        return self.multiEngine.reset(targets).addErrback(pickle.dumps, 2)
    
    def remote_keys(self, targets):
        return self.multiEngine.keys(targets).addErrback(pickle.dumps, 2)
    
    def remote_kill(self, targets, controller=False):
        return self.multiEngine.kill(targets, controller).addErrback(pickle.dumps, 2)
        
    def remote_pushSerialized(self, targets, pns):
        d = self.multiEngine.pushSerialized(targets, **pickle.loads(pns))
        return d.addErrback(pickle.dumps, 2)
    
    def remote_pullSerialized(self, targets, *keys):
        d = self.multiEngine.pullSerialized(targets, *keys)
        return d.addBoth(pickle.dumps, 2)
    
    def remote_clearQueue(self, targets):
        return self.multiEngine.clearQueue(targets).addErrback(pickle.dumps, 2)
    
    def remote_queueStatus(self, targets):
        return self.multiEngine.queueStatus(targets).addErrback(pickle.dumps, 2)

    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------

    def remote_getIDs(self):
        return self.multiEngine.getIDs()
    
    def remote_verifyTargets(self, targets):
        return self.multiEngine.verifyTargets(targets)
    
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
    
    def remote_scatter(self, targets, key, pseq, style='basic', flatten=False):
        seq = pickle.loads(pseq)
        d = self.multiEngine.scatter(targets, key, seq, style, flatten)
        return d.addErrback(pickle.dumps, 2)
    
    def remote_gather(self, targets, key, style='basic'):
        d = self.multiEngine.gather(targets, key, style)
        return d.addBoth(pickle.dumps, 2)
    

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
        
    def checkReturn(self, r):
        if isinstance(r, str):
            try: 
                return pickle.loads(r)
            except pickle.PickleError, TypeError: 
                pass
        elif isinstance(r, list):
            return map(self.checkReturn, r)
        return r
        
    #---------------------------------------------------------------------------
    # IEngineMultiplexer related methods
    #---------------------------------------------------------------------------
        
    def execute(self, targets, lines):
        d = self.callRemote('execute', targets, lines)
        return d.addCallback(self.checkReturn)
    
    def executeAll(self, lines):
        return self.execute('all', lines)
    
    def push(self, targets, **namespace):
        pns = pickle.dumps(namespace, 2)
        d = self.callRemote('push', targets, pns)
        return d.addCallback(self.checkReturn)
    
    def pushAll(self, **ns):
        return self.push('all', **ns)
    
    def pull(self, targets, *keys):
        return self.callRemote('pull', targets, *keys).addCallback(pickle.loads)
    
    def pullAll(self, *keys):
        return self.pull('all', *keys)
    
    def pullNamespace(self, targets, *keys):
        d = self.callRemote('pullNamespace', targets, *keys)
        return d.addCallback(pickle.loads)

    def pullNamespaceAll(self, *keys):
        return pullNamespace('all', *keys)
    
    def getResult(self, targets, i=None):
        d = self.callRemote('getResult', targets, i)
        return d.addCallback(self.checkReturn)
    
    def getResultAll(self, i=None):
        return self.getResult('all', i)
    
    def reset(self, targets):
        d = self.callRemote('reset', targets)
        return d.addCallback(self.checkReturn)
    
    def resetAll(self):
        return self.reset('all')
    
    def keys(self, targets):
        d = self.callRemote('keys', targets)
        return d.addCallback(self.checkReturn)
    
    def keysAll(self):
        return self.keys('all')
    
    def kill(self, targets, controller=False):
        d = self.callRemote('kill', targets, controller)
        return d.addCallback(self.checkReturn)
    
    def killAll(self, controller=False):
        return self.kill('all', controller)
    
    def pushSerialized(self, targets, **namespace):
        pns = pickle.dumps(namespace, 2)
        d = self.callRemote('pushSerialized', targets, pns)
        return d.addCallback(self.checkReturn)
    
    def pushSerializedAll(self, **namespace):
        return self.pushSerialized('all', **namespace)
    
    def pullSerialized(self, targets, *keys):
        d = self.callRemote('pullSerialized', targets, *keys)
        return d.addCallback(pickle.loads)
    
    def pullSerializedAll(self, *keys):
        return self.pullSerialized('all', *keys)
    
    def clearQueue(self, targets):
        d = self.callRemote('clearQueue', targets)
        return d.addCallback(self.checkReturn)
    
    def clearQueueAll(self):
        return self.clearQueue('all')
    
    def queueStatus(self, targets):
        d = self.callRemote('queueStatus', targets)
        return d.addCallback(self.checkReturn)
    
    def queueStatusAll(self):
        return self.queueStatus('all')
    
    #---------------------------------------------------------------------------
    # IMultiEngine related methods
    #---------------------------------------------------------------------------
    
    def getIDs(self):
        d = self.callRemote('getIDs')
        return d.addCallback(self.checkReturn)
    
    def verifyTargets(self, targets):
        d = self.callRemote('verifyTargets', targets)
        return d.addCallback(self.checkReturn)
    
    #---------------------------------------------------------------------------
    # IEngineCoordinator related methods
    #---------------------------------------------------------------------------
    
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        pseq = pickle.dumps(seq, 2)
        d = self.callRemote('scatter', targets, key, pseq, style, flatten)
        return d.addCallback(self.checkReturn)
    
    def gather(self, targets, key, style='basic'):
        d = self.callRemote('gather', targets, key, style='basic')
        return d.addCallback(pickle.loads)
    

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
        
    def connect(self):
        print "Connecting to ", self.addr
        self.factory = pb.PBClientFactory()
        d = self.factory.getRootObject()
        d.addCallback(self._gotRoot)
        reactor.connectTCP(self.addr[0], self.addr[1], self.factory)
        return blockOn(d)

    #---------------------------------------------------------------------------
    # Utility methods
    #---------------------------------------------------------------------------

    def disconnect(self):
        self.pbClient.disconnect()
        self.pbClient = None
        self.factory = None
            
    def _gotRoot(self, rootObj):
        print "Got root: ", rootObj
        self.pbClient = IMultiEngine(rootObj)
        return True

    def execute(self, targets, lines):
        return self.pbClient.execute(targets, lines)