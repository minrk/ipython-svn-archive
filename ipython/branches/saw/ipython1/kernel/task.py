# encoding: utf-8
# -*- test-case-name: ipython1.test.test_task -*-
"""Task farming representation of the controller.
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

import zope.interface as zi
from twisted.internet import defer
from twisted.python import components, log, failure

from ipython1.kernel import engineservice as es
from ipython1.kernel import controllerservice as cs

class IWorker(zi.Interface):
    
    def run(expression, resultName='', namespace={}):
        """Run expression in namespace."""
    

        
class WorkerFromQueuedEngine(object):
    
    zi.implements(IWorker)
    
    def __init__(self, qe):
        self.queuedEngine = qe
    
    def run(self, expression, resultName='', namespace={}):
        d1 = self.queuedEngine.push(**namespace)
        d1.addCallback(lambda r: self.queuedEngine.execute(expression))
        if resultName:
            d1.addCallback(lambda r: self.queuedEngine.pull(resultName))
        else:
            d1.addCallback(lambda r: None)
        return d1
    


class Task(object):
    """The task object for the Task Controller"""
    def __init__(self, taskID, expression, resultName, namespace={}, workerID=None):
        self.taskID = taskID
        self.workerID = workerID
        self.expression = expression
        self.resultName = resultName
        self.namespace = namespace
        self.deferred = defer.Deferred()

components.registerAdapter(WorkerFromQueuedEngine, es.IEngineQueued, IWorker)

class ITaskController(zi.Interface):
    
    def run(expression, resultName='', namespace=None):
        """Run a task"""
    
    def getTaskResult(taskID):
        """get a result"""

class TaskController(object):
    
    def __init__(self, controller):
        self.controller = controller
        self.controller.onRegisterEngineDo(self.registerWorker, True)
        self.controller.onUnregisterEngineDo(self.unregisterWorker, True)
        self.taskID = 0
        self.queue = [] # list of task objects
        self.pendingTasks = [] # list of (id, expression, namespace)
        self.results = {} # list of (id, result)
        self.workers = {}
        for id in self.controller.engines.keys():
                self.workers[id] = IWorker(self.controller.engines[id])
        self.idleWorkers = self.workers.keys()
    
    def registerWorker(self, id):
        """linked to controller.registerEngine"""
        if self.workers.get(id):
            raise "We already have one!  This should not happen"
        self.workers[id] = IWorker(self.controller.engines[id])
        self.idleWorkers.append(id)
        self.distributeTasks()
    
    def unregisterWorker(self, id):
        """linked to controller.registerEngine"""
        if self.workers.get(id):
            if id in self.idleWorkers:
                self.idleWorkers.remove(id)
            else:
                for task in self.pendingTasks:
                    if task.workerID == id:
                        # task.deferred.errback(failure.Failure(Exception("Worker Died"))
                        self.pendingTasks.remove(task)
                        task.deferred.errback(Exception("Worker Died"))
            del self.workers[id]
    
    #############
    # Interface methods
    #############
    
    def run(self, expression, resultName='', namespace={}):
        """returns a task ID and a deferred to its result"""
        empty = not self.queue
        taskID = self.taskID
        self.taskID += 1
        task = Task(taskID, expression, resultName, namespace)
        self.queue.append(task)
        log.msg('queuing task #%i' %taskID)
        self.distributeTasks()
        return taskID, task.deferred
    
    def getTaskResult(self, taskID):
        """returns a deferred to the result of a task"""
        if self.results.has_key(taskID):
            return defer.succeed(self.results[taskID])
        else:
            for task in self.pendingTasks+self.queue:
                if task.taskID == taskID:
                    return task.deferred
        return defer.fail(KeyError("task ID not registered"))
    
    #############
    # Queue methods
    #############
    
    def distributeTasks(self):
        # check for unassigned tasks and idle workers
        while self.queue and self.idleWorkers:
            # get worker
            workerID = self.idleWorkers.pop(0)
            # get from queue
            task = self.queue.pop(0)
            # add to pending
            self.pendingTasks.append(task)
            # run/link callbacks
            d = self.workers[workerID].run(task.expression, task.resultName, task.namespace)
            log.msg("running task #%i on worker %i" %(task.taskID, workerID))
            d.addBoth(self.taskCompleted, workerID, task.taskID).chainDeferred(task.deferred)
            
    
    def taskCompleted(self, result, workerID, taskID):
        """This is the callback for a completed task"""
        # remove from pending
        for i in range(len(self.pendingTasks)):
            if self.pendingTasks[i].taskID == taskID:
                self.pendingTasks.pop(i)
                break
        if isinstance(result, failure.Failure):
            log.msg("Task #%i failed"% taskID)
        else:    
            log.msg("Task #%i completed"% taskID)
        # add to results
        self.results[taskID] = result
        
        # get new task if exists and worker was not unregistered
        if workerID in self.workers.keys():
            self.idleWorkers.append(workerID)
            self.distributeTasks()
        
        # return result for callback chain purposes
        return result
    

components.registerAdapter(TaskController, cs.IControllerBase, ITaskController)