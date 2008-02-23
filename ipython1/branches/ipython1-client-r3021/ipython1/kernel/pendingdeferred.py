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
from ipython1.tools import guid, growl


class PendingDeferredManager(object):
    """A class to track pending deferreds.
    
    To track a pending deferred, the user of this class must first
    get a deferredID by calling `get_next_deferred_id`.  Then the user
    calls `save_pending_deferred` passing that id and the deferred to
    be tracked.  To later retrieve it, the user calls
    `get_pending_deferred` passing the id.
    """
    
    def __init__(self):
        """Manage pending deferreds."""

        self.pendingDeferreds = {}
        
    def get_next_deferred_id(self):
        """Get the next available deferred id.
        
        :Returns:
            deferredID : str
                The deferred id that the client should use for the next
                deferred is will save to me.
        """

        return guid.generate()
        
    def quick_has_id(self, deferred_id):
        return self.pendingDeferreds.has_key(deferred_id)
        
    def save_pending_deferred(self, deferredID, d, callback=None, args=None, kwargs=None):
        """Save a deferred to me by deferredID.
        
        :Parameters:
            deferredID : str
                A deferred id the client got by calling `get_next_deferred_id`.
            d : Deferred
                The deferred to save.
            callback : FunctionType
                A function to add to the callback of d before returning.
            arguments: tuple
                A two tuple of (args, kwargs) to pass to the function
        """
        pd = self.pendingDeferreds.get(deferredID)
        if pd is not None:
            self.remove_pending_deferred(deferredID)
        self.pendingDeferreds[deferredID] = (d, callback, args, kwargs)
        
    def remove_pending_deferred(self, deferredID):
        """Remove a deferred I am tracking and add a null Errback.
        
        :Parameters:
            deferredID : str
                The id of a deferred that I am tracking.
        """
        pd_tuple = self.pendingDeferreds.get(deferredID)
        if pd_tuple is not None:
            pd = pd_tuple[0]
            # Consume any remaining errors coming down the line.
            pd.addErrback(lambda f: None)
            del self.pendingDeferreds[deferredID]
    
    def clean_out_deferreds(self):
        """Remove all the deferreds I am tracking."""
        for k in self.pendingDeferreds.keys():
            self.remove_pending_deferred(k)
        
    def _deleteAndPassThrough(self, r, deferredID):
        self.remove_pending_deferred(deferredID)
        return r
        
    def get_pending_deferred(self, deferredID, block):
        """Get a pending deferred that I am tracking by deferredID.
        
        :Parameters:
            deferredID : int
                The id of a deferred I am tracking
            block : boolean
                Should I block until the deferred has fired.
        """
        (pd, cbfunc, cbfunc_args, cbfunc_kwargs) = self.pendingDeferreds.get(deferredID,(None,None,None,None))
        if pd is not None:
            if pd.called: # called
                if isinstance(pd.result, failure.Failure):
                    d_to_return = defer.fail(pd.result)
                elif isinstance(pd.result, defer.Deferred):
                    # This section is required because sometimes the original deferred (pd)
                    # has fired, but its result is another deferred, which has not yet fired.
                    if not block and not pd.result.called:
                        return defer.fail(failure.Failure(error.ResultNotCompleted("result not completed: %r" % deferredID)))
                    else:
                        # I am still not sure why I need to chain things in this way.
                        # But I know it works.
                        d_to_return = defer.Deferred()
                        pd.chainDeferred(d_to_return)
                else:
                    d_to_return = defer.succeed(pd.result)
            else: # not called
                if block:
                    pd.addCallback(self._deleteAndPassThrough, deferredID)
                    d_to_return = defer.Deferred()
                    pd.chainDeferred(d_to_return)
                else: # not block
                    return defer.fail(failure.Failure(error.ResultNotCompleted("result not completed: %r" % deferredID)))
            
            # Register the callback function with its args/kwargs if needed
            if cbfunc is not None:
                if cbfunc_args is None:
                    cbfunc_args = ()
                if cbfunc_kwargs is None:
                    cbfunc_kwargs = {}
                d_to_return.addCallback(cbfunc, *cbfunc_args, **cbfunc_kwargs)
                
            return d_to_return
        else:
            return defer.fail(failure.Failure(error.InvalidDeferredID('Invalid deferredID: ' + repr(deferredID))))
            
    def getAllPendingDeferreds(self):
        dList = []
        keys = self.pdManager.pendingDeferreds.keys()
        for k in keys:
            dList.append(self.pdManager.get_pending_deferred(k, block=True))
        if len(dList) > 0:  
            return gatherBoth(dList, consumeErrors=1)
        else:
            return defer.succeed([None])


def two_phase(wrappedMethod):
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
        try:
            block = kwargs.pop('block')
        except KeyError:
            block = True  # The default if not specified
        if block:
            return wrappedMethod(pendingDeferredManager, *args, **kwargs)
        else:
            deferredID = pendingDeferredManager.get_next_deferred_id()
            d = wrappedMethod(pendingDeferredManager, *args, **kwargs)
            pendingDeferredManager.save_pending_deferred(deferredID, d)
            return defer.succeed(deferredID)
    
    return wrapperTwoPhase
                
                
            
            
                
        