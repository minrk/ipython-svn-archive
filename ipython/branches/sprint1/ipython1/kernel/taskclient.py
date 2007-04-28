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

# from twisted.python import failure

from ipython1.kernel import task

#-------------------------------------------------------------------------------
# Connecting Task Client
#-------------------------------------------------------------------------------

class InteractiveTaskClient(object):
    """XML-RPC version of the Connecting TaskControllerClient"""
    
    ############
    # ConnectingTaskController
    ############
    def irun(self, *args, **kwargs):
        """call with a task object"""
        block = kwargs.pop('block', self.block)
        if len(args) == 1 and isinstance(args[0], task.Task):
            t = args[0]
        else:
            t = task.Task(*args, **kwargs)
        taskID = self.run(t)
        print "TaskID = %i"%taskID
        return self.getTaskResult(taskID, block)
        # return tr
