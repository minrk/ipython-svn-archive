# encoding: utf-8
# -*- test-case-name: ipython1.kernel.test.test_pendingdeferred -*-
"""Classes to manage pending Deferreds.

A pending deferred is a deferred that may or may not have fired.  This module
is useful for taking a class whose methods return deferreds and wrapping it to
provide API that keeps track of those deferreds for later retrieval.  See the
tests for examples of its usage.
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

from ipython1.kernel.twistedutil import gatherBoth
from ipython1.kernel import error
from ipython1.tools import guid


class PendingDeferredManager(object):
    """A class to track pending deferreds.
    
    To track a pending deferred, the user of this class must first
    get a deferredID by calling `getNextDeferredID`.  Then the user
    calls `savePendingDeferred` passing that id and the deferred to
    be tracked.  To later retrieve it, the user calls
    `getPendingDeferred` passing the id.
    """
    
    def __init__(self):
        """Manage pending deferreds."""

        self.pendingDeferreds = {}
        
    def getNextDeferredID(self):
        """Get the next available deferred id.
        
        :Returns:
            deferredID : str
                The deferred id that the client should use for the next
                deferred is will save to me.
        """

        return guid.generate()
        
    def savePendingDeferred(self, deferredID, d):
        """Save a deferred to me by deferredID.
        
        :Parameters:
            deferredID : str
                A deferred id the client got by calling `getNextDeferredID`.
            d : Deferred
                The deferred to save.
        """
        
        pd = self.pendingDeferreds.get(deferredID)
        if pd is not None:
            self.removePendingDeferred(deferredID)
        self.pendingDeferreds[deferredID] = d
        
    def removePendingDeferred(self, deferredID):
        """Remove a deferred I am tracking and add a null Errback.
        
        :Parameters:
            deferredID : str
                The id of a deferred that I am tracking.
        """
        
        pd = self.pendingDeferreds.get(deferredID)
        if pd is not None:
            pd.addErrback(lambda f: None)
            del self.pendingDeferreds[deferredID]
        
    def cleanOutDeferreds(self):
        """Remove all the deferreds I am tracking."""
        for k in self.pendingDeferreds.keys():
            self.removePendingDeferred(k)
        
    def _deleteAndPassThrough(self, r, deferredID):
        self.removePendingDeferred(deferredID)
        return r
        
    def getPendingDeferred(self, deferredID, block):
        """Get a pending deferred that I am tracking by deferredID.
        
        :Parameters:
            deferredID : int
                The id of a deferred I am tracking
            block : boolean
                Should I block until the deferred has fired.
        """
        #log.msg("getPendingDeferred: %s %s" % (repr(deferredID), repr(block)))
        pd = self.pendingDeferreds.get(deferredID)
        if pd is not None:
            if not pd.called and block:    # pd has not fired and we should block
                #log.msg("pendingDeferred has not been called: %s" % deferredID)
                pd.addCallback(self._deleteAndPassThrough, deferredID)
                return pd
            elif not pd.called and not block: # pd has not fired, but we should not block
                return defer.fail(failure.Failure(error.ResultNotCompleted("Result not completed: %i" % deferredID)))
            else:    # pd has fired
                #log.msg("pendingDeferred has been called: %s: %s" % (deferredID, repr(pd.result)))
                if isinstance(pd.result, failure.Failure):
                    dToReturn = defer.fail(pd.result)
                elif isinstance(pd.result, defer.Deferred):
                    dToReturn = pd.result
                else:
                    dToReturn = defer.succeed(pd.result)
                # It has fired so remove it!
                self.removePendingDeferred(deferredID)
            return dToReturn
        else:
            return defer.fail(failure.Failure(error.InvalidDeferredID('Invalid deferredID: ' + repr(deferredID))))
            
    def getAllPendingDeferreds(self):
        dList = []
        keys = self.pdManager.pendingDeferreds.keys()
        for k in keys:
            dList.append(self.pdManager.getPendingDeferred(k, block=True))
        if len(dList) > 0:  
            return gatherBoth(dList, consumeErrors=1)
        else:
            return defer.succeed([None])


def twoPhase(wrappedMethod):
    """Wrap methods that return a deferred into a two phase process.
    
    This transforms::
    
        foo(arg1, arg2, ...) -> foo(block, arg1, arg2, ...).
    
    The wrapped method will then return a deferred to a deferredID.  This will
    only work on method of classes that inherit from `PendingDeferredManager`,
    as that class provides an API for 
    
    block is a boolean to determine if we should use the two phase process or
    just simply call the wrapped method.  At this point block does not have a
    default and it probably won't.
    """
    
    def wrapperTwoPhase(pendingDeferredManager, *args, **kwargs):
        block = args[0]
        if block:
            return wrappedMethod(pendingDeferredManager, *args[1:], **kwargs)
        else:
            deferredID = pendingDeferredManager.getNextPendingDeferredID()
            d = wrappedMethod(pendingDeferredManager, *args[1:], **kwargs)
            pendingDeferredManager.savePendingDeferred(deferredID, d)
            return defer.succeed(deferredID)
       
                
    return wrapperTwoPhase
                
                
            
            
                
        