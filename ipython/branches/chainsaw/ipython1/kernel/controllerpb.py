# encoding: utf-8
# -*- test-case-name: ipython1.test.test_controllerpb -*-
"""A Perspective Broker interface to a ControllerService.

This class lets PB clients talk to the ControllerService.  The main difficulty
is that PB doesn't allow arbitrary objects to be sent over the wire - only
basic Python types.  To get around this we simple pickle more complex objects
on boths side of the wire.  That is the main thing these classes have to 
manage.

To do:

 * remote_addNotifier is not in the ControllerService implem. or interf.
 * PBNotifierChild need documentation.
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

from twisted.python import components
from twisted.python.failure import Failure
from twisted.spread import pb
from zope.interface import Interface, implements

from ipython1.kernel import controllerservice as cs, results


#-------------------------------------------------------------------------------
# The Controller side of things
#-------------------------------------------------------------------------------

class IPBController(Interface):
    """Perspective Broker interface to controller.  
    
    The methods in this interface are similar to those from IMultiEngine, 
    but their arguments and return values are pickled if they are not already
    simple Python types so they can be send over PB.  This is to deal with 
    the fact that w/o a lot of work PB cannot send arbitrary objects over the
    wire.

    See the documentation of IMultiEngine for documentation about the methods.
    """
            
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
        
    def remote_status(targets):
        """"""
        
    def remote_kill(targets):
        """"""
        
    def remote_pushSerialized(targets, **namespace):
        """"""
        
    def remote_pullSerialized(targets, *keys):
        """"""
        
    def remote_clearQueue(targets):
        """"""
        
    def remote_verifyTargets(targets):
        """"""
    
    def remote_getIDs():
        """"""
        
    def remote_scatter(targets, key, seq, style='basic', flatten=False):
        """"""
        
    def remote_gather(targets, key, style='basic'):
        """"""
        
    def remote_addNotifier(reference):    
        """"""
        
        
class PBControllerRootFromService(pb.Root):
    """Perspective Broker interface to controller.
    
    See IPBController and IMultiEngine for documentation. 
    """
    
    implements(IPBController)
    
    def __init__(self, cs):
        self.service = cs
    
    def remote_execute(self, targets, lines):
        d = self.service.execute(targets, lines)
        return d.addErrback(pickle.dumps, 2)
    
    def remote_push(self, targets, pns):
        d = self.service.push(targets, **pickle.loads(pns))
        return d.addErrback(pickle.dumps, 2)
    
    def remote_pull(self, targets, *keys):
        return self.service.pull(targets, *keys).addBoth(pickle.dumps, 2)
    
    def remote_pullNamespace(self, targets, *keys):
        d = self.service.pullNamespace(targets, *keys)
        return d.addBoth(pickle.dumps, 2)
    
    def remote_getResult(self, targets, i=None):
        d = self.service.getResult(targets, i).addCallback(self.checkReturns)
        return d.addErrback(pickle.dumps, 2)
    
    def remote_reset(self, targets):
        return self.service.reset(targets).addErrback(pickle.dumps, 2)
    
    def remote_status(self, targets):
        return self.service.status(targets).addErrback(pickle.dumps, 2)
    
    def remote_kill(self, targets):
        return self.service.kill(targets).addErrback(pickle.dumps, 2)
        
    def remote_pushSerialized(self, targets, pns):
        d = self.service.pushSerialized(targets, **pickle.loads(pns))
        return d.addErrback(pickle.dumps, 2)
    
    def remote_pullSerialized(self, targets, *keys):
        d = self.service.pullSerialized(targets, *keys)
        return d.addBoth(pickle.dumps, 2)
    
    def remote_clearQueue(self, targets):
        return self.service.clearQueue(targets).addErrback(pickle.dumps, 2)
    
    def remote_verifyTargets(self, targets):
        return self.service.verifyTargets(targets)
    
    def remote_getIDs(self):
        return self.service.getIDs()
    
    def remote_scatter(self, targets, key, pseq, style='basic', flatten=False):
        seq = pickle.loads(pseq)
        d = self.service.scatter(targets, key, seq, style, flatten)
        return d.addErrback(pickle.dumps, 2)
    
    def remote_gather(self, targets, key, style='basic'):
        d = self.service.gather(targets, key, style)
        return d.addBoth(pickle.dumps, 2)
    
    def remote_addNotifier(self, reference):
        """Adds a notifier.
        
        Should this in the one of the Controller interfaces?
        """
        
        n = results.INotifierChild(reference)
        return self.service.addNotifier(n)
    
    def checkReturns(self, rlist):
        for r in rlist:
            if isinstance(r, (Failure, Exception)):
                rlist[rlist.index(r)] = pickle.dumps(r, 2)
        return rlist


components.registerAdapter(PBControllerRootFromService,
            cs.ControllerService, IPBController)


class IPBControllerFactory(Interface):
    pass
    
    
def PBServerFactoryFromService(service):
    """Adapt a ControllerService to a PBServerFactory.
    
    Is there a reason this is a function rather than a class?
    """
    
    return pb.PBServerFactory(IPBController(service))
    
    
components.registerAdapter(PBServerFactoryFromService,
            cs.ControllerService, IPBControllerFactory)
        

#-------------------------------------------------------------------------------
# The Client side of things
#-------------------------------------------------------------------------------

class PBRemoteController(pb.Referenceable, results.NotifierParent):
    """Adapt a PB ref to a remote ControllerService to an IMultiEngine implementer.
    """
    
    implements(cs.IMultiEngine)
    
    def __init__(self, reference):
        self.reference = reference
        self.callRemote = reference.callRemote
        cs.addAllMethods(self)
        self.deferred = self.callRemote('addNotifier', self)
        self.remote_notify = self.notify
        
    def execute(self, targets, lines):
        d = self.callRemote('execute', targets, lines)
        return d.addCallback(self.checkReturn)
    
    def push(self, targets, **namespace):
        pns = pickle.dumps(namespace, 2)
        d = self.callRemote('push', targets, pns)
        return d.addCallback(self.checkReturn)
    
    def pull(self, targets, *keys):
        return self.callRemote('pull', targets, *keys).addCallback(pickle.loads)
    
    def pullNamespace(self, targets, *keys):
        d = self.callRemote('pullNamespace', targets, *keys)
        return d.addCallback(pickle.loads)
    
    def getResult(self, targets, i=None):
        d = self.callRemote('getResult', targets, i)
        return d.addCallback(self.checkReturn)
    
    def reset(self, targets):
        d = self.callRemote('reset', targets)
        return d.addCallback(self.checkReturn)
    
    def status(self, targets):
        d = self.callRemote('status', targets)
        return d.addCallback(self.checkReturn)
    
    def kill(self, targets):
        d = self.callRemote('kill', targets)
        return d.addCallback(self.checkReturn)
    
    def pushSerialized(self, targets, **namespace):
        pns = pickle.dumps(namespace, 2)
        d = self.callRemote('pushSerialized', targets, pns)
        return d.addCallback(self.checkReturn)
    
    def pullSerialized(self, targets, *keys):
        d = self.callRemote('pullSerialized', targets, *keys)
        return d.addCallback(pickle.loads)
    
    def clearQueue(self, targets):
        d = self.callRemote('clearQueue', targets)
        return d.addCallback(self.checkReturn)
    
    def verifyTargets(self, targets):
        d = self.callRemote('verifyTargets', targets)
        return d.addCallback(self.checkReturn)
    
    def getIDs(self):
        d = self.callRemote('getIDs')
        return d.addCallback(self.checkReturn)
    
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        pseq = pickle.dumps(seq, 2)
        d = self.callRemote('scatter', targets, key, pseq, style, flatten)
        return d.addCallback(self.checkReturn)
    
    def gather(self, targets, key, style='basic'):
        d = self.callRemote('gather', targets, key, style='basic')
        return d.addCallback(pickle.loads)
    
    def checkReturn(self, r):
        if isinstance(r, str):
            try: 
                return pickle.loads(r)
            except pickle.PickleError, TypeError: 
                pass
        elif isinstance(r, list):
            return map(self.checkReturn, r)
        return r


components.registerAdapter(PBRemoteController, 
        pb.RemoteReference, cs.IMultiEngine)
    
    
class PBNotifierChild(results.BaseNotifierChild):
    """Can we document this class?"""
    
    def __init__(self, reference):
        self.key = repr(reference)
        self.callRemote = reference.callRemote
        reference.broker.notifyOnDisconnect(self.onDisconnect)
    
    def notify(self, result):
        return self.callRemote('notify', result).addErrback(self.onDisconnect)
    
    
components.registerAdapter(PBNotifierChild,
        pb.RemoteReference, results.INotifierChild)

