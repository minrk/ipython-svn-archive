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
from twisted.internet import defer, reactor
from twisted.python import components, log, failure

from ipython1.kernel import engineservice as es
from ipython1.kernel import controllerservice as cs
from ipython1.kernel.pendingdeferred import PendingDeferredAdapter, twoPhase
from ipython1.kernel.util import gatherBoth

def _printer(r):
    print "_print: ",r
    return r

class Task(object):
    """The task object for the Task Controller
    init requires string expression to be executed.
    @resultNames: string or list of strings that are the names of objects to be
    pulled as results.  If not specified, will return {'result', None}
    @setupNS: a dict of objects to be pushed before execution of the expression
        if not specified, nothing will be pushed
    @clearBefore: boolean for whether to clear the namespace before running the job
        default: False
    @clearAfter: boolean for whether to clear the namespace after running the job
        default: False
    @retries: int number of times to resubmit the task if it fails.
        default: 0
    @options: any other keyword options for more elaborate uses of tasks"""
    def __init__(self, expression, resultNames=None, setupNS={},
            clearBefore=False, clearAfter=False, retries=0, **options):
        self.expression = expression
        if isinstance(resultNames, str):
            self.resultNames = [resultNames]
        else:
            self.resultNames = resultNames
        self.setupNS = setupNS
        self.clearBefore = clearBefore
        self.clearAfter = clearAfter
        self.retries=retries
        self.options = options
    

class IWorker(zi.Interface):
    
    def run(task):
        """Run task in namespace."""
    

class WorkerFromQueuedEngine(object):
    
    zi.implements(IWorker)
    
    def __init__(self, qe):
        self.queuedEngine = qe
    
    def run(self, task):
        """run a task, return a deferred to its result"""
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
        """callback for constructing the results dict"""
        for r in rlist:
            if isinstance(r, failure.Failure):
                return r
        if len(names) == 1:
            return {names[0]:rlist[index]}
        return dict(zip(names, rlist[index]))
    

components.registerAdapter(WorkerFromQueuedEngine, es.IEngineQueued, IWorker)

class ITaskController(cs.IControllerBase):
    """The Task based interface to a Controller object"""
    
    def run(task):
        """Run a task"""
    
    def getTaskResult(taskID):
        """get a result"""

class TaskController(cs.ControllerAdapterBase):
    """The Task based interface to a Controller object"""
    
    zi.implements(ITaskController)
    
    def __init__(self, controller):
        self.controller = controller
        self.controller.onRegisterEngineDo(self.registerWorker, True)
        self.controller.onUnregisterEngineDo(self.unregisterWorker, True)
        self.taskID = 0
        self.failurePenalty = 1 # the time in seconds to penalize
                                # a worker for failing a task
        self.queue = [] # list of task objects
        self.pendingTasks = {} # dict of {workerID:(taskID, task)}
        self.deferredResults = {} # dict of {taskID:deferred}
        self.finishedResults = {} # dict of {taskID:actualResult}
        self.workers = {} # dict of {workerID:worker}
        for id in self.controller.engines.keys():
                self.workers[id] = IWorker(self.controller.engines[id])
        self.idleWorkers = self.workers.keys()
    
    def registerWorker(self, id):
        """called by controller.registerEngine"""
        if self.workers.get(id):
            raise "We already have one!  This should not happen"
        self.workers[id] = IWorker(self.controller.engines[id])
        if not self.pendingTasks.has_key(id):
            self.idleWorkers.append(id)
        self.distributeTasks()
    
    def unregisterWorker(self, id):
        """called by controller.unregisterEngine"""
        if self.workers.has_key(id):
            if id in self.idleWorkers:
                self.idleWorkers.remove(id)
            elif self.pendingTasks.has_key(id):
                pass
            self.workers.pop(id)
    
    #---------------------------------------------------------------------------
    # Interface methods
    #---------------------------------------------------------------------------
    
    def run(self, task):
        """returns a task ID and a deferred to its TaskResult"""
        taskID = self.taskID
        self.taskID += 1
        d = defer.Deferred()
        self.queue.append((taskID, task))
        log.msg('queuing task #%i' %taskID)
        # d.addErrback(self.resubmit, task, taskID)
        d.addBoth(lambda r: (taskID, r))
        self.deferredResults[taskID] = d
        self.distributeTasks()
        return defer.succeed(taskID)
    
    def getTaskResult(self, taskID):
        """returns a deferred to a (taskID, result) tuple"""
        log.msg("getting result %i"%taskID)
        if self.finishedResults.has_key(taskID):
            return defer.succeed((taskID, self.finishedResults[taskID]))
        elif self.deferredResults.has_key(taskID):
            return self.deferredResults[taskID]
        else:
            return defer.succeed((taskID, KeyError("task ID not registered")))
    
    #---------------------------------------------------------------------------
    # Queue methods
    #---------------------------------------------------------------------------
    
    def distributeTasks(self):
        # check for unassigned tasks and idle workers
        while self.queue and self.idleWorkers:
            # get worker
            workerID = self.idleWorkers.pop(0)
            # get task
            (taskID, task) = self.queue.pop(0)
            # add to pending
            self.pendingTasks[workerID] = (taskID, task)
            # run/link callbacks
            # d2 = self.deferredResults[taskID]
            d = self.workers[workerID].run(task)
            log.msg("running task #%i on worker %i" %(taskID, workerID))
            d.addBoth(self.taskCompleted, workerID)
            # d.addBoth(self.resubmit, task, taskID)
            # d.chainDeferred(d2)
            
    def taskCompleted(self, result, workerID):
        """This is the err/callback for a completed task"""
        taskID, task = self.pendingTasks.pop(workerID)
        # d = None
        if isinstance(result, failure.Failure): # we failed
            log.msg("Task #%i failed"% taskID)
            if task.retries > 0: # resubmit
                task.retries -= 1
                self.queue.append((taskID, task))
                s = "resubmitting task #%i, %i retries remaining" %(taskID, task.retries)
                log.msg(s)
                self.distributeTasks()
            else: # done trying
                d = self.deferredResults.pop(taskID)
                self.finishedResults[taskID] = result
                d.callback(result)
            # wait a second before readmitting a worker that failed
            # it may have died, and not yet been unregistered
            reactor.callLater(self.failurePenalty, self.readmitWorker, workerID)
        else: # we succeeded
            log.msg("Task #%i completed"% taskID)
            d = self.deferredResults.pop(taskID)
            self.finishedResults[taskID] = result
            d.callback(result)
            self.readmitWorker(workerID)
    
    def readmitWorker(self, workerID):
        """readmit a worker to the idleWorkers.  This is outside taskCompleted
        because of the failurePenalty being implemented through 
        reactor.callLater"""
        if workerID in self.workers.keys():
            self.idleWorkers.append(workerID)
            self.distributeTasks()
        
    
components.registerAdapter(TaskController, cs.IControllerBase, ITaskController)

class ISynchronousTaskController(zi.Interface):
    pass

class SynchronousTaskController(PendingDeferredAdapter):
    
    zi.implements(ISynchronousTaskController)
    
    def __init__(self, taskController):
        self.taskController = taskController
        PendingDeferredAdapter.__init__(self)
    
    #---------------------------------------------------------------------------
    # Decorated pending deferred methods
    #---------------------------------------------------------------------------
    
    # @twoPhase
    def run(self, task):
        return self.taskController.run(task)
    
    @twoPhase
    def getTaskResult(self, taskID):
        return self.taskController.getTaskResult(taskID)
    

components.registerAdapter(SynchronousTaskController, ITaskController, 
                                ISynchronousTaskController)
