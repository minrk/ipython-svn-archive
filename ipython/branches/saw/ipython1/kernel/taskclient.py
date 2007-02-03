# encoding: utf-8
# -*- test-case-name: ipython1.test.test_taskcontrollerxmlrpc -*-
"""The Generic Task Client object.  This must be subclassed based on your 
connection method.
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

from twisted.python import failure

from ipython1.kernel import task, blockon, util

#-------------------------------------------------------------------------------
# Connecting Task Client
#-------------------------------------------------------------------------------

class ConnectingTaskClient(object):
    """XML-RPC version of the Connecting TaskControllerClient"""
    
    def __init__(self, addr):
        self.addr = addr
        self.taskcontroller = None
        self.block = False
        self.connected = False
        self.pendingDeferreds = set()
        self.caughtFailures = []
    
    def _catchFailure(self, f):
        return f
    
    def _passThrough(self,r,d):
        self.pendingDeferreds.discard(d)
        if isinstance(r, failure.Failure):
            self.caughtFailures.append(r)
        return r
    
    def __defer__(self):
        """for blockOn(this)"""
        return util.DeferredList(list(self.pendingDeferreds))
    
    def _blockOrNot(self, d):
        if self.block:
            return self.blockOn(d)
        else:
            return d
    
    def connect(self):
        """sublcass and override this"""
        
    def run(self, *args, **kwargs):
        """call with a task object"""
        self.connect()
        block = kwargs.pop('block', self.block)
        if len(args) == 1 and isinstance(args[0], task.Task):
            t = args[0]
        else:
            t = task.Task(*args, **kwargs)
        tr = self.taskcontroller.run(t)
        self.pendingDeferreds.add(tr.result)
        tr.result.addBoth(self._passThrough, tr.result)
        if block:
            return self.blockOn(tr)
        else:
            return tr
    
    def getTaskResult(self, taskID):
        self.connect()
        tr = self.taskcontroller.getTaskResult(taskID)
        self.pendingDeferreds.add(tr.result)
        tr.result.addBoth(self._passThrough, tr.result)
        return self._blockOrNot(tr)
    
    def blockOn(self, d):
        return blockon.blockOn(d)
    
