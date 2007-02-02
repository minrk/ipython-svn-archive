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

from ipython1.kernel import task, blockon

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
        (taskID, d) = self.taskcontroller.run(t)
        if block:
            return taskID, self.blockOn(d)
        else:
            return taskID, d
        return taskID, self._blockOrNot(d)
    
    def getTaskResult(self, taskID):
        self.connect()
        return self._blockOrNot(self.taskcontroller.getTaskResult(taskID))
    
    def blockOn(self, d):
        return blockon.blockOn(d)
    
