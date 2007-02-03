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

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

class ResubmittedTask(Exception):
    pass

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
    

class TaskResult(object):
    """The object that contains the result of a task"""
    def __init__(self, taskID=None, result=None):
        self.taskID = taskID
        self.result = result
    
    def __defer__(self):
        return self.result
    

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
        self.pendingTasks = {} # dict of {workerID:(taskID, task)}
        self.deferredResults = {} # dict of {taskID:TaskResult}
        self.finishedResults = {} # dict of {taskID:actualResult}
        self.workers = {} # dict of {workerID:worker}
        for id in self.controller.engines.keys():
                self.workers[id] = IWorker(self.controller.engines[id])
        self.idleWorkers = self.workers.keys()
    
    def registerWorker(self, id):
        """linked to controller.registerEngine"""
        if self.workers.get(id):
            raise "We already have one!  This should not happen"
        self.workers[id] = IWorker(self.controller.engines[id])
        if not self.pendingTasks.has_key(id):
            self.idleWorkers.append(id)
        self.distributeTasks()
    
    def unregisterWorker(self, id):
        """linked to controller.registerEngine"""
        if self.workers.has_key(id):
            if id in self.idleWorkers:
                self.idleWorkers.remove(id)
            elif self.pendingTasks.has_key(id):
                pass
            self.workers.pop(id)
    
    #############
    # Interface methods
    #############
    
    def run(self, task):
        """returns a task ID and a deferred to its result"""
        taskID = self.taskID
        self.taskID += 1
        tresult = TaskResult(taskID, defer.Deferred())
        self.queue.append((taskID, task))
        log.msg('queuing task #%i' %taskID)
        tresult.result.addErrback(self.resubmit, task, taskID)
        self.deferredResults[taskID] = tresult
        self.distributeTasks()
        return tresult
    
    def resubmit(self, r, task, taskID):
        """an errback for a failed task"""
        if task.retries > 0:
            task.retries -= 1
            self.queue.append((taskID, task))
            s = "resubmitting task #%i, %i retries remaining" %(taskID, task.retries)
            log.msg(s)
            d = defer.Deferred().addErrback(self.resubmit, task, taskID)
            # the previous result deferred is now stale
            # self.deferredResults[taskID].result.addErrback(lambda _:None)
            # use the new one
            self.deferredResults[taskID].result = d
            self.distributeTasks()
            return d
        else:
            return r
    
    def getTaskResult(self, taskID):
        """returns a deferred to the result of a task"""
        if self.finishedResults.has_key(taskID):
            return TaskResult(taskID, defer.succeed(self.finishedResults[taskID]))
        elif self.deferredResults.has_key(taskID):
            return self.deferredResults[taskID]
        else:
            return TaskResult(taskID, defer.fail(KeyError("task ID not registered")))
    
    #############
    # Queue methods
    #############
    
    def distributeTasks(self):
        # check for unassigned tasks and idle workers
        while self.queue and self.idleWorkers:
            # get worker
            workerID = self.idleWorkers.pop(0)
            # get from queue
            (taskID, task) = self.queue.pop(0)
            # add to pending
            self.pendingTasks[workerID] = (taskID, task)
            # run/link callbacks
            d2 = self.deferredResults[taskID].result
            d = self.workers[workerID].run(task)
            # d.addErrback(self.resubmit, task, taskID)
            # d.addErrback(self.check)
            log.msg("running task #%i on worker %i" %(taskID, workerID))
            d.addBoth(self.taskCompleted, workerID, taskID)
            d.chainDeferred(d2)
            
    
    def taskCompleted(self, result, workerID, taskID):
        """This is the err/callback for a completed task"""
        task = self.pendingTasks.pop(workerID)[1]
        if isinstance(result, failure.Failure): # we failed
            log.msg("Task #%i failed"% taskID)
            if task.retries < 1: # but we are done trying
                self.finishedResults[taskID] = result
                result = None
        else: # we succeeded
            log.msg("Task #%i completed"% taskID)
            self.finishedResults[taskID] = result
            # self.deferredResults.pop(taskID).result.addErrback(lambda _:None)
        
        # get new task if exists and worker was not unregistered
        if workerID in self.workers.keys():
            self.idleWorkers.append(workerID)
            self.distributeTasks()
        
        #pass through result for callbacks
        return result

    

components.registerAdapter(TaskController, cs.IControllerBase, ITaskController)