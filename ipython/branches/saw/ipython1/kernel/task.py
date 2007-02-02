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
from ipython1.kernel.util import gatherBoth


class Task(object):
    """The task object for the Task Controller"""
    def __init__(self, expression, taskID=None, resultNames=None, setupNS={},
            clearBefore=False, clearAfter=False, retries=0):
        self.taskID = taskID
        self.expression = expression
        if isinstance(resultNames, str):
            self.resultNames = [resultNames]
        else:
            self.resultNames = resultNames
        self.setupNS = setupNS
        self.clearBefore = clearBefore
        self.clearAfter = clearAfter
        self.retries=retries
        self.deferred = defer.Deferred()
    

class IWorker(zi.Interface):
    
    def run(task):
        """Run expression in namespace."""
    

class WorkerFromQueuedEngine(object):
    
    zi.implements(IWorker)
    
    def __init__(self, qe):
        self.queuedEngine = qe
    
    def run(self, task):
        """run a task, return a deferred to its results"""
        dl = []
        index = 1
        if task.clearBefore:
            dl.append(self.queuedEngine.reset())
            index += 1
        if task.setupNS:
            dl.append(self.queuedEngine.push(**task.setupNS))
            index += 1
        
        dl.append(self.queuedEngine.execute(task.expression))
        
        if task.resultNames:
            d = self.queuedEngine.pull(*task.resultNames)
        else:
            d = defer.succeed(None)
        dl.append(d)
        if task.clearAfter:
            dl.append(self.queuedEngine.reset())
        
        names = task.resultNames or ['result']
        d = gatherBoth(dl, consumeErrors = True)
        return d.addBoth(self.zipResults, names, index)
    
    def zipResults(self, rlist, names, index):
        for r in rlist:
            if isinstance(r, failure.Failure):
                return r
        if len(names) == 1:
            return {names[0]:rlist[index]}
        return dict(zip(names, rlist[index]))
    

components.registerAdapter(WorkerFromQueuedEngine, es.IEngineQueued, IWorker)

class ITaskController(zi.Interface):
    
    def run(task):
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
        self.pendingTasks = {} # dict of {workerID:task}
        self.results = {} # dict of {id:result}
        self.workers = {} # dict of {workerID:worker}
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
        if self.workers.has_key(id):
            if id in self.idleWorkers:
                self.idleWorkers.remove(id)
            elif self.pendingTasks.has_key(id):
                task = self.pendingTasks.pop(id)
                # if not task.deferred.called:
                #     task.deferred.errback(failure.Failure(Exception("Worker Died")))
            self.workers.pop(id)
    
    #############
    # Interface methods
    #############
    
    def run(self, task):
        """returns a task ID and a deferred to its result"""
        task.taskID = self.taskID
        self.taskID += 1
        self.queue.append(task)
        log.msg('queuing task #%i' %task.taskID)
        self.distributeTasks()
        return task.taskID, task.deferred.addErrback(self.resubmit, task)
    
    def resubmit(self, r, task):
        if task.retries:
            task.retries -= 1
            task.deferred = defer.Deferred().addErrback(self.resubmit, task)
            self.queue.append(task)
            log.msg("resubmitting task #%i, %i retries remaining"\
                                %(task.taskID, task.retries))
            self.distributeTasks()
            return task.deferred
        else:
            return r
    
    def getTaskResult(self, taskID):
        """returns a deferred to the result of a task"""
        if self.results.has_key(taskID):
            return defer.succeed(self.results[taskID])
        else:
            for task in self.pendingTasks.values()+self.queue:
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
            self.pendingTasks[workerID] = task
            # run/link callbacks
            d = self.workers[workerID].run(task)
            log.msg("running task #%i on worker %i" %(task.taskID, workerID))
            d.addBoth(self.taskCompleted, workerID, task.taskID).chainDeferred(task.deferred)
            
    
    def taskCompleted(self, result, workerID, taskID):
        """This is the err/callback for a completed task"""
        # remove from pending
        for key, task in self.pendingTasks.iteritems():
            if task.taskID == taskID:
                task = self.pendingTasks.pop(key)
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