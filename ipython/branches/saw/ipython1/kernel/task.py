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

from ipython1.kernel import engineservice as es, error
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

class IScheduler(zi.Interface):
    """The interface for a scheduler"""
    
    def addTask(task, taskID):
        """add a (taskID, task) to the task queue"""
    
    def popTask(id=None):
        """pops a (taskID, task) tuple, the highest priority by default
        if @i is specified, pops task corresponding to taskID
        if no such task is registered, raises index error
        """
    
    def addWorker(worker, workerID):
        """add (workerID, worker) to the worker queue"""
    
    def popWorker(id=None):
        """pops a (workerID, worker) tuple, the highest priority by default
        if @i is specified, pops worker corresponding to workerID
        if no such worker is registered, raises index error
        """
    
    def ready():
        """returns True if there is something to do, False otherwise"""
    

class FIFOScheduler(object):
    """A basic First-In-First-Out (queue) Scheduler"""
    
    def __init__(self):
        self.tasks = []
        self.workers = []
    
    def addTask(self, task, taskID):
        """add a (taskID, task) to the task queue"""
        self.tasks.append((taskID, task))
    
    def popTask(self, id=None):
        """pops a (taskID, task) tuple, the highest priority by default
        if @i is specified, pops task corresponding to taskID
        if no such task is registered, raises index error
        """
        if id is None:
            return self.tasks.pop(0)
        else:
            for i in range(len(self.tasks)):
                taskID = self.tasks[i][0]
                if id == taskID:
                    return self.tasks.pop(i)
            raise IndexError("No task #%i"%id)
    
    def addWorker(self, worker, workerID):
        """add a (workerID, worker) to the worker queue"""
        self.workers.append((workerID, worker))
    
    def popWorker(self, id=None):
        """pops a (workerID, worker) tuple, the highest priority by default
        if @i is specified, pops worker corresponding to workerID
        if no such worker is registered, raises index error
        """
        if id is None:
            return self.workers.pop(0)
        else:
            for i in range(len(self.workers)):
                workerID = self.workers[i][0]
                if id == workerID:
                    return self.workers.pop(i)
            raise IndexError("No worker #%i"%id)
    
    def ready(self):
        return bool(self.workers and self.tasks)

class ITaskController(cs.IControllerBase):
    """The Task based interface to a Controller object"""
    
    def run(task):
        """Run a task"""
    
    def getTaskResult(taskID):
        """get a result"""
    
    def abort(taskID):
        """remove task from queue if task is has not been submitted."""

class TaskController(cs.ControllerAdapterBase):
    """The Task based interface to a Controller object.
    If you want to use a different scheduler, just subclass this and set
    the 'Scheduler' member to the *class* of your scheduler."""
    
    zi.implements(ITaskController)
    Scheduler = FIFOScheduler
    
    def __init__(self, controller):
        self.controller = controller
        self.controller.onRegisterEngineDo(self.registerWorker, True)
        self.controller.onUnregisterEngineDo(self.unregisterWorker, True)
        self.taskID = 0
        self.failurePenalty = 1 # the time in seconds to penalize
                                # a worker for failing a task
        self.pendingTasks = {} # dict of {workerID:(taskID, task)}
        self.deferredResults = {} # dict of {taskID:deferred}
        self.finishedResults = {} # dict of {taskID:actualResult}
        self.workers = {} # dict of {workerID:worker}
        self.abortPending = [] # list of [(taskID, abortDeferred)]
        for id in self.controller.engines.keys():
                self.workers[id] = IWorker(self.controller.engines[id])
        self.scheduler = self.Scheduler()
        for id, worker in self.workers.iteritems():
            self.scheduler.addWorker(worker, id)
    
    def registerWorker(self, id):
        """called by controller.registerEngine"""
        if self.workers.get(id):
            raise "We already have one!  This should not happen."
        self.workers[id] = IWorker(self.controller.engines[id])
        if not self.pendingTasks.has_key(id):# if not working
            self.scheduler.addWorker(self.workers[id], id)
        self.distributeTasks()
    
    def unregisterWorker(self, id):
        """called by controller.unregisterEngine"""
        if self.workers.has_key(id):
            try:
                self.scheduler.popWorker(id)
            except IndexError:
                pass
            self.workers.pop(id)
    
    def _pendingTaskIDs(self):
        return [t[0] for t in self.pendingTasks.values()]
    
    def _abortedTaskIDs(self):
        return [t[0] for t in self.abortPending]
    
    #---------------------------------------------------------------------------
    # Interface methods
    #---------------------------------------------------------------------------
    
    def run(self, task):
        """returns a task ID and a deferred to its TaskResult"""
        taskID = self.taskID
        self.taskID += 1
        d = defer.Deferred()
        self.scheduler.addTask(task, taskID)
        log.msg('queuing task #%i' %taskID)
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
            return defer.succeed((taskID, IndexError("task ID not registered")))
    
    def abort(self, taskID):
        """remove a task from the queue if it has not been run already"""
        try:
            self.scheduler.popTask(taskID)
        except IndexError, e:
            if taskID in self.finishedResults.keys():
                d = defer.fail(IndexError("Task Already Completed"))
            elif taskID in self._pendingTaskIDs():# task is pending
                for id, d in self.abortPending:
                    if taskID == id:# already aborted
                        return d
                d = defer.Deferred()
                self.abortPending.append((taskID, d))
            else:
                return defer.fail(e)
        else:
            self._reallyAbort(taskID)
            d = defer.succeed(None)
        return d
    
    def _reallyAbort(self, taskID):
        for i in range(len(self.abortPending)):
            id,d = self.abortPending[i]
            if taskID == id:
                d.callback(None)
                self.abortPending.pop(i)
                d2 = self.deferredResults.pop(taskID)
                log.msg("Task #%i Aborted"%taskID)
                e = error.TaskAborted()
                result = failure.Failure(e)
                self.finishedResults[taskID] = result
                d2.errback(result)
                return
        raise IndexError("Failed to Abort task #%i"%taskID)
    
    #---------------------------------------------------------------------------
    # Queue methods
    #---------------------------------------------------------------------------
    
    def distributeTasks(self):
        # check for unassigned tasks and idle workers
        while self.scheduler.ready():
            # get worker
            workerID, worker = self.scheduler.popWorker()
            # get task
            taskID, task = self.scheduler.popTask()
            # add to pending
            self.pendingTasks[workerID] = (taskID, task)
            # run/link callbacks
            # d2 = self.deferredResults[taskID]
            d = worker.run(task)
            log.msg("running task #%i on worker %i" %(taskID, workerID))
            d.addBoth(self.taskCompleted, taskID, workerID)
            # d.addBoth(self.resubmit, task, taskID)
            # d.chainDeferred(d2)
            
    def taskCompleted(self, result, taskID, workerID):
        """This is the err/callback for a completed task"""
        try:
            taskID, task = self.pendingTasks.pop(workerID)
        except:
            # this should not happen
            log.msg("tried to pop bad pending task#%i from worker #%i"%(taskID, workerID))
            log.msg("result: %s"%result)
            log.msg("pending tasks:%s"%self.pendingTasks)
            return
        
        # Check if aborted while pending
        aborted = False
        for id, d in self.abortPending:
            if taskID == id:
                self._reallyAbort(taskID)
                aborted = True
                break
        
        if not aborted:
            if isinstance(result, failure.Failure): # we failed
                log.msg("Task #%i failed on worker %i"% (taskID, workerID))
                if task.retries > 0: # resubmit
                    task.retries -= 1
                    self.scheduler.addTask(task, taskID)
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
                log.msg("Task #%i completed "% taskID)
                d = self.deferredResults.pop(taskID)
                self.finishedResults[taskID] = result
                d.callback(result)
                self.readmitWorker(workerID)
        else:# we aborted the task
            if isinstance(result, failure.Failure): # it failed
                reactor.callLater(self.failurePenalty, self.readmitWorker, workerID)
            else:
                self.readmitWorker(workerID)
    
    def readmitWorker(self, workerID):
        """readmit a worker to the idleWorkers.  This is outside taskCompleted
        because of the failurePenalty being implemented through 
        reactor.callLater"""
        if workerID in self.workers.keys() and workerID not in self.pendingTasks.keys():
            self.scheduler.addWorker(self.workers[workerID],workerID)
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
    
    def run(self, task):
        return self.taskController.run(task)
    
    @twoPhase
    def abort(self, taskID):
        return self.taskController.abort(taskID)
    
    @twoPhase
    def getTaskResult(self, taskID):
        return self.taskController.getTaskResult(taskID)
    

components.registerAdapter(SynchronousTaskController, ITaskController, 
                                ISynchronousTaskController)
