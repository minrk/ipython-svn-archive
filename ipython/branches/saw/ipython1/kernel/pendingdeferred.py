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
            pd.addErrback(log.err)
            del self.pendingDeferreds[deferredID]
        
    def cleanOutDeferreds(self):
        for k in self.pendingDeferreds.iterkeys():
            self.removePendingDeferred(k)
        
    def getPendingDeferred(self, deferredID):
        pd = self.pendingDeferreds.get(deferredID)
        if pd is not None:
            if not pd.called:    # pd has not fired
                log.msg("pendingDeferred has not been called: %s" % deferredID)
                pd.addCallback(lambda _: self.removePendingDeferred(deferredID))
                return pd
            else:                # pd has fired
                log.msg("pendingDeferred has been called: %s: %s" % (deferredID, repr(pd.result)))
                if isinstance(pd.result, failure.Failure):
                    dToReturn = defer.fail(pd.result)
                else:
                    dToReturn = defer.succeed(pd.result)
                # It has fired so remove it!
                self.removePendingDeferred(deferredID)
            return dToReturn
        else:
            return defer.fail(failure.Failure(error.InvalidDeferredID('Invalid deferredID: ' + repr(deferredID))))
            
class TwoPhase(object):
    """Wrap methods that return a deferred into a two phase process.
    
    This transforms foo(arg1, arg2, ...) -> foo(clientID, block, arg1, arg2, ...).
    
    :Parameters:
        - `clientID`: The ID of the client making the request
        - `block`:  Boolean that determines if a two phase process is not used.
        
    At this point block does not have a default and it probably won't.
    """
    
    def __init__(self, pendingDeferredAdapter, wrappedMethod):
        self.wrappedMethod = wrappedMethod
        self.pendingDeferredAdapter = pendingDeferredAdapter

    def __call__(self, *args, **kwargs):
        clientID = args[0]
        block = args[1]
        if self.pendingDeferredAdapter._isValidClientID(clientID):
            if block:
                return self.wrappedMethod(*args[2:], **kwargs)
            else:
                deferredID = self.pendingDeferredAdapter.getNextPendingDeferredID(clientID)
                d = self.wrappedMethod(*args[2:], **kwargs)
                self.pendingDeferredAdapter.savePendingDeferred(clientID, deferredID, d)
                return defer.succeed(deferredID)
        else:  
            return defer.fail(failure.Failure(
                error.InvalidClientID("Client with ID %i has not been registered." % clientID)))        


class IPendingDeferredAdapter(Interface):
    pass

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
        
    def getPendingDeferred(self, clientID, deferredID):
        if self._isValidClientID(clientID):
            return self.pdManagers[clientID].getPendingDeferred(deferredID)
        else:
            return defer.fail(failure.Failure(
                error.InvalidClientID("Client with ID %i has not been registered." % clientID)))
                
    def getAllPendingDeferreds(self, clientID):
        dList = []
        for k in self.pdManagers[clientID].pendingDeferreds.iterkeys():
            dList.append(pbManagers[clientID].getPendingDeferred(k))
        return gatherBoth(dList, consumeErrors=1)
