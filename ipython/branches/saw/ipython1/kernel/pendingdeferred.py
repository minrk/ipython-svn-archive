# encoding: utf-8
# -*- test-case-name: ipython1.test.test_pendingdeferred -*-
"""Classes to manage pending Deferreds.
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

from twisted.application import service
from twisted.internet import defer, reactor
from twisted.python import log, components, failure
from zope.interface import Interface, implements, Attribute

from ipython1.kernel.util import gatherBoth
from ipython1.kernel import error


class PendingDeferredManager(object):
    
    def __init__(self, clientID):
        self.clientID = clientID
        self.deferredID = 0
        self.pendingDeferreds = {}
        
    def getNextDeferredID(self):
        did = self.deferredID
        self.deferredID += 1
        return did
        
    def savePendingDeferred(self, deferredID, d):
        pd = self.pendingDeferreds.get(deferredID)
        if pd is not None:
            self.removePendingDeferred(deferredID)
        self.pendingDeferreds[deferredID] = d
        
    def removePendingDeferred(self, deferredID):
        pd = self.pendingDeferreds.get(deferredID)
        if pd is not None:
            pd.addErrback(lambda f: None)
            del self.pendingDeferreds[deferredID]
        
    def cleanOutDeferreds(self):
        for k in self.pendingDeferreds.iterkeys():
            self.removePendingDeferred(k)
        
    def _deleteAndPassThrough(self, r, deferredID):
        self.removePendingDeferred(deferredID)
        return r
        
    def getPendingDeferred(self, deferredID, block):
        pd = self.pendingDeferreds.get(deferredID)
        if pd is not None:
            if not pd.called and block:    # pd has not fired and we should block
                #log.msg("pendingDeferred has not been called: %s" % deferredID)
                pd.addCallback(self._deleteAndPassThrough, deferredID)
                return pd
            elif not pd.called and not block:
                return defer.fail(failure.Failure(error.ResultNotCompleted("Result not completed: %i" % deferredID)))
            else:                          # pd has fired, but we shouldn't block for it
                #log.msg("pendingDeferred has been called: %s: %s" % (deferredID, repr(pd.result)))
                if isinstance(pd.result, failure.Failure):
                    dToReturn = defer.fail(pd.result)
                else:
                    dToReturn = defer.succeed(pd.result)
                # It has fired so remove it!
                self.removePendingDeferred(deferredID)
            return dToReturn
        else:
            return defer.fail(failure.Failure(error.InvalidDeferredID('Invalid deferredID: ' + repr(deferredID))))
            

def twoPhase(wrappedMethod):
    """Wrap methods that return a deferred into a two phase process.
    
    This transforms foo(arg1, arg2, ...) -> foo(clientID, block, arg1, arg2, ...).
    
    :Parameters:
        - `clientID`: The ID of the client making the request
        - `block`:  Boolean that determines if a two phase process is not used.
        
    At this point block does not have a default and it probably won't.
    """
    
    def wrapperTwoPhase(pendingDeferredAdapter, *args, **kwargs):
        clientID = args[0]
        block = args[1]
        if pendingDeferredAdapter._isValidClientID(clientID):
            if block:
                return wrappedMethod(pendingDeferredAdapter, *args[2:], **kwargs)
            else:
                deferredID = pendingDeferredAdapter.getNextPendingDeferredID(clientID)
                d = wrappedMethod(pendingDeferredAdapter, *args[2:], **kwargs)
                pendingDeferredAdapter.savePendingDeferred(clientID, deferredID, d)
                return defer.succeed(deferredID)
        else:  
            return defer.fail(failure.Failure(
                error.InvalidClientID("Client with ID %r has not been registered." % clientID)))        
                
    return wrapperTwoPhase

class IPendingDeferredAdapter(Interface):
    
    def getNextPendingDeferredID(clientID):
        """"""
        
    def savePendingDeferred(clientID, deferredID, d):
        """"""

class PendingDeferredAdapter(object):
    
    implements(IPendingDeferredAdapter)
    
    def __init__(self):
        self.clientID = 0
        self.pdManagers = {}
        
    #---------------------------------------------------------------------------
    # Internal methods
    #---------------------------------------------------------------------------
        
    def _isValidClientID(self, clientID):
        if self.pdManagers.has_key(clientID):
            return True
        else:
            return False
            
    def getNextPendingDeferredID(self, clientID):
        """Get the next deferredId for clientID.
        
        The caller of this method must first call _isValidClientID to verfiy that
        clientID is valid.
        """
        return self.pdManagers[clientID].getNextDeferredID()
 
        
    def savePendingDeferred(self, clientID, deferredID, d):
        """Save d for clientID under deferredID.
        
        The caller of this method must first call _isValidClientID to verfiy that
        clientID is valid.        
        """
        return self.pdManagers[clientID].savePendingDeferred(deferredID, d)
 
        
    #---------------------------------------------------------------------------
    # Methods related to pending deferreds
    #---------------------------------------------------------------------------
        
    def registerClient(self):
        cid = self.clientID
        self.clientID += 1
        self.pdManagers[cid] = PendingDeferredManager(cid)
        return cid
        
    def unregisterClient(self, clientID):
        if self._isValidClientID(clientID):
            self.pdManagers[clientID].cleanOutDeferreds()
            del self.pdManagers[clientID]
        else:
            raise error.InvalidClientID("Client with ID %i has not been registered." % clientID)
        
    def getPendingDeferred(self, clientID, deferredID, block):
        if self._isValidClientID(clientID):
            return self.pdManagers[clientID].getPendingDeferred(deferredID, block)
        else:
            return defer.fail(failure.Failure(
                error.InvalidClientID("Client with ID %i has not been registered." % clientID)))
                
    def getAllPendingDeferreds(self, clientID):
        dList = []
        keys = self.pdManagers[clientID].pendingDeferreds.keys()
        for k in keys:
            dList.append(self.pdManagers[clientID].getPendingDeferred(k, block=True))
        if len(dList) > 0:  
            return gatherBoth(dList, consumeErrors=1)
        else:
            return defer.succeed([None])