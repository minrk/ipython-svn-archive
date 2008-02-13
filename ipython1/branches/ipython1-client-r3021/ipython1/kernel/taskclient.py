# encoding: utf-8
# -*- test-case-name: ipython1.kernel.test.test_taskcontrollerxmlrpc -*-
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

from zope.interface import Interface, implements
from twisted.python import components, log

from ipython1.kernel.twistedutil import blockingCallFromThread
from ipython1.kernel import task, error

#-------------------------------------------------------------------------------
# Connecting Task Client
#-------------------------------------------------------------------------------

class InteractiveTaskClient(object):
    
    def irun(self, *args, **kwargs):
        """Run a task on the `TaskController`.
        
        This method is a shorthand for run(task) and its arguments are simply
        passed onto a `Task` object:
        
        irun(*args, **kwargs) -> run(Task(*args, **kwargs))

        :Parameters:
            expression : str
                A str that is valid python code that is the task.
            resultNames : str or list of str 
                The names of objects to be pulled as results.
            setupNS : dict
                A dict of objects to be pushed into the engines namespace before
                execution of the expression.
            clearBefore : boolean
                Should the engine's namespace be cleared before the task is run.
                Default=False.
            clearAfter : boolean 
                Should the engine's namespace be cleared after the task is run.
                Default=False.
            retries : int
                The number of times to resumbit the task if it fails.  Default=0.
            options : dict
                Any other keyword options for more elaborate uses of tasks
            
        :Returns: A `TaskResult` object.      
        """
        block = kwargs.pop('block', False)
        if len(args) == 1 and isinstance(args[0], task.Task):
            t = args[0]
        else:
            t = task.Task(*args, **kwargs)
        taskID = self.run(t)
        print "TaskID = %i"%taskID
        if block:
            return self.getTaskResult(taskID, block)
        else:
            return taskID

class IBlockingTaskClient(Interface):
    pass


class BlockingTaskClient(InteractiveTaskClient):
    
    implements(IBlockingTaskClient)
    
    def __init__(self, task_controller):
        self.task_controller = task_controller
        self.block = True
        
    def run(self, task):
        return blockingCallFromThread(self.task_controller.run, task)
    
    def getTaskResult(self, taskID, block=False):
        return blockingCallFromThread(self.task_controller.getTaskResult,
            taskID, block)
    
    def abort(self, taskID):
        return blockingCallFromThread(self.task_controller.abort, taskID)
    
    def barrier(self, taskIDs):
        return blockingCallFromThread(self.task_controller.barrier, taskIDs)
    
    def spin(self):
        return blockingCallFromThread(self.task_controller.spin)

components.registerAdapter(BlockingTaskClient,
            task.ITaskController, IBlockingTaskClient)


