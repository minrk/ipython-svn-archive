# encoding: utf-8
# -*- test-case-name: ipython1.test.test_task -*-
"""Task farming representation of the ControllerService.
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

from types import FunctionType as function

import zope.interface as zi, string
from twisted.internet import defer, reactor
from twisted.python import components, log, failure

from ipython1.kernel import engineservice as es, error
from ipython1.kernel import controllerservice as cs
from ipython1.kernel.pendingdeferred import PendingDeferredAdapter, twoPhase
from ipython1.kernel.util import gatherBoth, DeferredList

class Task(object):
    """Our representation of a task for the `TaskController` interface.

    The user should create instances of this class to represent a task that 
    needs to be done.
    
    :Parameters:
        expression : str
            A str that is valid python code that is the task.
        resultNames : str or list of str 
            The names of objects to be pulled as results.  If not specified, 
            will return {'result', None}
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
        recoveryTask : Task
            This is the Task to be run when the task has exhausted its retries
            Default=None.
        depends : Dependency, dict, list, str
            This is the dependency structure for the Task, which determines
            whether a task can be run on a Worker.  If depends is given as
            a dict, list, or str, then it is passed to the constructor
            for a Dependency.  See the Dependency doc for details.
            Default=None
        options : dict
            Any other keyword options for more elaborate uses of tasks
    
    Examples
    --------
    
    >>> t = Task('dostuff(args)')
    >>> t = Task('a=5', resultNames='a')
    >>> t = Task('a=5\nb=4', resultNames=['a','b'])
    >>> t = Task('os.kill(os.getpid(),9)', retries=100) # this is a bad idea
    """
    def __init__(self, expression, resultNames=None, setupNS=None,
            clearBefore=False, clearAfter=False, retries=0, 
            recoveryTask=None, depends=None, **options):
        self.expression = expression
        if isinstance(resultNames, str):
            self.resultNames = [resultNames]
        else:
            self.resultNames = resultNames
        self.setupNS = setupNS
        self.clearBefore = clearBefore
        self.clearAfter = clearAfter
        self.retries=retries
        self.recoveryTask = recoveryTask
        if depends is None:
            self.dependency = _Dependency()
        elif isinstance(depends, Dependency):
            self.dependency = depends
        else:
            self.dependency = Dependency(depends)
        self.options = options
        self.taskID = None

class resultNS:
    """The result namespace object for use in TaskResult objects as tr.ns.
    It builds an object from a dictionary, such that it has attributes
    according to the key,value pairs of the dictionary.
    
    This works by calling setattr on ALL key,value pairs in the dict.  If a user
    chooses to overwrite the `__repr__` or `__getattr__` attributes, they can.
    This can be a bad idea, as it may corrupt standard behavior of the
    ns object.
    
    Example
    --------
    
    >>> ns = resultNS({'a':17,'foo':range(3)})
    >>> print ns
        NS{'a':17,'foo':range(3)}
    >>> ns.a
        17
    >>> ns['foo']
        [0,1,2]
    """
    def __init__(self, dikt):
        for k,v in dikt.iteritems():
            setattr(self,k,v)
    
    def __repr__(self):
        l = dir(self)
        d = {}
        for k in l:
            # do not print private objects
            if k[:2] != '__' and k[-2:] != '__':
                d[k] = getattr(self, k)
        return "NS"+repr(d)
    
    def __getitem__(self, key):
        return getattr(self, key)

class TaskResult(object):
    """An object for returning task results.
        
        This object encapsulates the results of a task.  On task
        success it will have a keys attribute that will have a list
        of the variables that have been pulled back.  These variables
        are accessible as attributes of this class as well.  On 
        success the failure attribute will be None.
        
        In task failure, keys will be empty, but failure will contain
        the failure object that encapsulates the remote exception.
        One can also simply call the raiseException() method of 
        this class to re-raise any remote exception in the local
        session.
        
        The TaskResult has a .ns member, which is a property for access
        to the results.  If the Task had resultNames=['a', 'b'], then the 
        Task Result will have attributes tr.ns.a, tr.ns.b for those values.
        Accessing tr.ns will raise the remote failure if the task failed.
        
        The engineID attribute should have the engineID of the engine
        that ran the task.  But, because engines can come and go in
        the ipython task system, the engineID may not continue to be
        valid or accurate.
        
        The taskID attribute simply gives the taskID that the task
        is tracked under.
    """
    taskID = None
    
    def _getNS(self):
        if isinstance(self.failure, failure.Failure):
            return self.failure.raiseException()
        else:
            return self._ns
    
    def _setNS(self, v):
        raise Exception("I am protected!")
    
    ns = property(_getNS, _setNS)
    
    def __init__(self, results, engineID):
        self.engineID = engineID
        if isinstance(results, failure.Failure):
            self.failure = results
            self.results = {}
        else:
            self.results = results
            self.failure = None
        
        self._ns = resultNS(self.results)
        
        self.keys = self.results.keys()
    
    def __repr__(self):
        if self.failure is not None:
            contents = self.failure
        else:
            contents = self.results
        return "TaskResult[ID:%r]:%r"%(self.taskID, contents)
    
    def __getitem__(self, key):
        if self.failure is not None:
            self.raiseException()
        return self.results[key]
    
    def raiseException(self):
        """Re-raise any remote exceptions in the local python session."""
        if self.failure is not None:
            self.failure.raiseException()


class _Dependency(object):
    """an empty Dependency that provides only the `test` method, 
    for defaulting in a Task"""
    def test(self, properties):
        return True
    

class Dependency(_Dependency):
    """an object to enable elaborate dependency tests against the properites
    of a worker.
    Standard form is a list of the form [(key, value, test),].  The primary
    method of this object is this.test(properties), where properties is a 
    dictionary of the properties of a worker.  Tests are made of the form:
    if properties.get(key) `test` value: True
    this.test() will return True if 
    
    `key` is a string, by which values will be pulled from the properties dict.
    `value` is the target value against which the property is tested.
        Default: True
    `test` is a simple comparison operator: '==', '<', '>=' etc.
        Default: '=='
    
    a Dependency object can be constructed with a dict, list, or string:
    >>>d = Dependency(dict(a=True,b='asdf'))
        is equivalent to:
    >>>d = Dependency([('a', True, '=='), ('b', 'asdf', '==')])
        is equivalent to:
    >>>d = Dependency(['a', ('b', 'asdf')])
    another example:
    >>>d = Dependency([('memory', '2GB', '>=')])
    >>>d.test(properties)
        will only return true of properties.get('memory') >= '2GB'
    
    string construction is different.  String construction allows the user
    to define an analytic test function in one of two ways.
    First, a function called test, taking one argument, and returning True|False
    >>>d = Dependency('''def test(properties):
                ...
                return True # or False
                ''')
    or a boolean expression in terms of a dict called 'properties':
    >>>d = Dependency("properties['a'] == True and properties['mem'] > '1GB'")
    
    dependencies can be added through d.depend(key, value, test) in the same way
    as the constructor, unless the dependency was constructed from a string.
    >>>d.depends(['a', ('b', False)])
        is equivalent to
    >>>d.depends('a') # also d.depends('a', True, '==')
    >>>d.depends('b', False)
    
    """
    
    def __init__(self, init=None):
        self.dependencies = []
        if init is None:
            return
        if isinstance(init, (dict, list, tuple)):
            self.depend(init)
        elif isinstance(init, str):
            if "def test" not in init:
                self.dependencies = "def test(properties):  return %s"%init
            else:
                self.dependencies = init
            # check for valid dependency string
            exec(self.dependencies)
            try:
                test({})
            except Exception, e:
                raise TypeError("Bad Strtest: %r"%e)
            self.test = self.strtest
        else:
            raise TypeError("Dependencies incorrectly formatted")
    
    def depend(self, key, value=True, test='=='):
        assert isinstance(self.dependencies, list), "cannot edit dependencies of strtest"
        if isinstance(key, dict):
            [self.depend(k, v, '==') for k,v in key.iteritems()]
        elif isinstance(key, (list, tuple)):
            for d in key:
                if isinstance(d, (list, tuple)):
                    self.depend(*d)
                elif isinstance(d, str):
                    self.depend(d)
                else:
                    raise TypeError("Bad Dependency list:%s"%key)
        else:
            self.dependencies.append((key, value, test))
    
    def undepend(self, key):
        assert isinstance(self.dependencies, list), "cannot edit dependencies of strtest"
        zipd = zip(*self.dependencies)
        if key in zipd[0]:
            self.dependencies.pop(list(zipd[0]).index(key))
    
    def test(self, properties):
        for key, target, test in self.dependencies:
            c = cmp(properties.get(key), target)
            if c == 0 and '=' in test:
                continue
            elif c == 1 and '>' in test:
                continue
            elif c == -1 and '<' in test:
                continue
            else:
                return False
        return True
    
    def strtest(self, properties):
        exec self.dependencies
        try:
            return test(properties)
        except Exception, e:
            log.msg("maybe bad strtest: %r"%e)
            return False

class IWorker(zi.Interface):
    """The Basic Worker Interface. 
    
    A worked is a representation of an Engine that is ready to run tasks.
    """
    def run(task):
        """Run task in worker's namespace.
        
        :Parameters:
            task : a `Task` object
        
        :Returns: `Deferred` to a `TaskResult` object.
        """
    

class WorkerFromQueuedEngine(object):
    """Adapt an `IQueuedEngine` to an `IWorker` object"""
    zi.implements(IWorker)
    
    def __init__(self, qe):
        self.queuedEngine = qe
        self.workerID = None
    
    def getProperties(self):
        return self.queuedEngine.properties
    
    properties = property(getProperties, lambda self, _:None)
    
    def run(self, task):
        """Run task in worker's namespace.
        
        :Parameters:
            task : a `Task` object
        
        :Returns: `Deferred` to a `TaskResult` object.
        """
        if task.clearBefore:
            d = self.queuedEngine.reset()
        else:
            d = defer.succeed(None)
            
        if task.setupNS is not None:
            d.addCallback(lambda r: self.queuedEngine.push(**task.setupNS))
        
        d.addCallback(lambda r: self.queuedEngine.execute(task.expression))
        
        if task.resultNames is not None:
            d.addCallback(lambda r: self.queuedEngine.pull(*task.resultNames))
        else:
            d.addCallback(lambda r: None)
        
        def reseter(result):
            self.queuedEngine.reset()
            return result
            
        if task.clearAfter:
            d.addBoth(reseter)
        
        return d.addBoth(self._zipResults, task.resultNames)
    
    def _zipResults(self, result, names):
        """Callback for construting the TaskResult object."""
        if isinstance(result, failure.Failure):
            return TaskResult(result, self.queuedEngine.id)
        else:
            if names is None:
                resultDict = {} 
            elif len(names) == 1:
                resultDict = {names[0]:result}
            else:
                resultDict = dict(zip(names, result))
        return TaskResult(resultDict, self.queuedEngine.id)

components.registerAdapter(WorkerFromQueuedEngine, es.IEngineQueued, IWorker)

class IScheduler(zi.Interface):
    """The interface for a Scheduler.
    """
    zi.Attribute("nworkers", "the number of unassigned workers")
    zi.Attribute("ntasks", "the number of unscheduled tasks")
    
    def addTask(task, **flags):
        """Add a task to the queue of the Scheduler.
        
        :Parameters:
            task : a `Task` object
                The task to be queued.
            flags : dict
                General keywords for more sophisticated scheduling
        """
    
    def popTask(id=None):
        """Pops a Task object.
        
        This gets the next task to be run.  If no `id` is requested, the highest priority
        task is returned.
        
        :Parameters:
            id
                The id of the task to be popped.  The default (None) is to return 
                the highest priority task.
                
        :Returns: a `Task` object
        
        :Exceptions:
            IndexError : raised if no taskID in queue
        """
    
    def addWorker(worker, **flags):
        """Add a worker to the worker queue.
        
        :Parameters:
            worker : an IWorker implementing object
            flags : General keywords for more sophisticated scheduling
        """
    
    def popWorker(id=None):
        """Pops an IWorker object that is ready to do work.
        
        This gets the next IWorker that is ready to do work. 
        
        :Parameters:
            id : if specified, will pop worker with workerID=id, else pops
                 highest priority worker.  Defaults to None.
        
        :Returns:
            an IWorker object
        
        :Exceptions:
            IndexError : raised if no workerID in queue
        """
    
    def ready():
        """Returns True if there is something to do, False otherwise"""
    
    def schedule():
        """Returns a tuple of the worker and task pair for the next
        task to be run.
        """
    

class FIFOScheduler(object):
    """A basic First-In-First-Out (Queue) Scheduler.
    This is the default Scheduler for the TaskController.
    See the docstrings for IScheduler for interface details.
    """
    
    zi.implements(IScheduler)
    
    def __init__(self):
        self.tasks = []
        self.workers = []
    
    def _ntasks(self):
        return len(self.tasks)
    
    def _nworkers(self):
        return len(self.workers)
    
    ntasks = property(_ntasks, lambda self, _:None)
    nworkers = property(_nworkers, lambda self, _:None)
    
    def addTask(self, task, **flags):    
        self.tasks.append(task)
    
    def popTask(self, id=None):
        if id is None:
            return self.tasks.pop(0)
        else:
            for i in range(len(self.tasks)):
                taskID = self.tasks[i].taskID
                if id == taskID:
                    return self.tasks.pop(i)
            raise IndexError("No task #%i"%id)
    
    def addWorker(self, worker, **flags):
        self.workers.append(worker)
    
    def popWorker(self, id=None):
        if id is None:
            return self.workers.pop(0)
        else:
            for i in range(len(self.workers)):
                workerID = self.workers[i].workerID
                if id == workerID:
                    return self.workers.pop(i)
            raise IndexError("No worker #%i"%id)
    
    def schedule(self):
        for t in self.tasks:
            for w in self.workers:
                try:# do not allow exceptions to break this
                    cando = t.dependency.test(w.properties)
                except:
                    cando = False
                if cando:
                    return self.popWorker(w.workerID), self.popTask(t.taskID)
        return None, None
    


class LIFOScheduler(FIFOScheduler):
    """A Last-In-First-Out (Stack) Scheduler.  This scheduler should naively
    reward fast engines by giving them more jobs.  This risks starvation, but
    only in cases with low load, where starvation does not really matter.
    """
    
    def addTask(self, task, **flags):
        self.tasks.reverse()
        self.tasks.append(task)
        self.tasks.reverse()
    
    def addWorker(self, worker, **flags):
        self.workers.reverse()
        self.workers.append(worker)
        self.workers.reverse()
    

class ITaskController(cs.IControllerBase):
    """The Task based interface to a `ControllerService` object
    
    This adapts a `ControllerService` to the ITaskController interface.
    """
    
    def run(task):
        """Run a task.
        
        :Parameters:
            task : an IPython `Task` object
        
        :Returns: the integer ID of the task
        """
    
    def getTaskResult(taskID):
        """Get the result of a task by its ID.
        
        :Parameters:
            taskID : int
                the id of the task whose result is requested
        
        :Returns: `Deferred` to (taskID, actualResult) if the task is done, and None
            if not.
        
        :Exceptions:
            actualResult will be an `IndexError` if no such task has been submitted
        """
    
    def abort(taskID):
        """Remove task from queue if task is has not been submitted.
        
        If the task has already been submitted, wait for it to finish and discard 
        results and prevent resubmission.
        
        :Parameters:
            taskID : the id of the task to be aborted
        
        :Returns:
            `Deferred` to abort attempt completion.  Will be None on success.
        
        :Exceptions:
            deferred will fail with `IndexError` if no such task has been submitted
            or the task has already completed.
        """
    
    def barrier(taskIDs):
        """Block until the list of taskIDs are completed.
        
        Returns None on success.
        """
    
    def spin():
        """touch the scheduler, to resume scheduling without submitting
        a task.
        """
    

class TaskController(cs.ControllerAdapterBase):
    """The Task based interface to a Controller object.
    
    If you want to use a different scheduler, just subclass this and set
    the `SchedulerClass` member to the *class* of your chosen scheduler.
    """
    
    zi.implements(ITaskController)
    SchedulerClass = FIFOScheduler
    
    timeout = 30
    
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
        self.abortPending = [] # dict of {taskID:abortDeferred}
        self.idleLater = None # delayed call object for timeout
        self.scheduler = self.SchedulerClass()
        
        for id in self.controller.engines.keys():
                self.workers[id] = IWorker(self.controller.engines[id])
                self.workers[id].workerID = id
                self.schedule.addWorker(self.workers[id])
    
    def registerWorker(self, id):
        """Called by controller.registerEngine."""
        if self.workers.get(id):
            raise "We already have one!  This should not happen."
        self.workers[id] = IWorker(self.controller.engines[id])
        self.workers[id].workerID = id
        if not self.pendingTasks.has_key(id):# if not working
            self.scheduler.addWorker(self.workers[id])
        self.distributeTasks()
    
    def unregisterWorker(self, id):
        """Called by controller.unregisterEngine"""
        
        if self.workers.has_key(id):
            try:
                self.scheduler.popWorker(id)
            except IndexError:
                pass
            self.workers.pop(id)
    
    def _pendingTaskIDs(self):
        return [t.taskID for t in self.pendingTasks.values()]
    
    #---------------------------------------------------------------------------
    # Interface methods
    #---------------------------------------------------------------------------
    
    def run(self, task):
        """Run a task and return `Deferred` to its taskID."""
        task.taskID = self.taskID
        self.taskID += 1
        d = defer.Deferred()
        self.scheduler.addTask(task)
        log.msg('queuing task #%i' %task.taskID)
        
        self.deferredResults[task.taskID] = []
        self.distributeTasks()
        return defer.succeed(task.taskID)
    
    def getTaskResult(self, taskID, block=False):
        """Returns a `Deferred` to a TaskResult tuple or None."""
        log.msg("getting result %i"%taskID)
        if self.finishedResults.has_key(taskID):
            tr = self.finishedResults[taskID]
            return defer.succeed(tr)
        elif self.deferredResults.has_key(taskID):
            if block:
                d = defer.Deferred()
                self.deferredResults[taskID].append(d)
                return d
            else:
                return defer.succeed(None)
        else:
            return defer.fail(IndexError("task ID not registered: %r" % taskID))
    
    def abort(self, taskID):
        """Remove a task from the queue if it has not been run already."""
        try:
            self.scheduler.popTask(taskID)
        except IndexError, e:
            if taskID in self.finishedResults.keys():
                d = defer.fail(IndexError("Task Already Completed"))
            elif taskID in self.abortPending:
                d = defer.fail(IndexError("Task Already Aborted"))
            elif taskID in self._pendingTaskIDs():# task is pending
                self.abortPending.append(taskID)
                d = defer.succeed(None)
            else:
                d = defer.fail(e)
        else:
            d = defer.execute(self._doAbort, taskID)
        
        return d
    
    def barrier(self, taskIDs):
        dList = []
        for id in taskIDs:
            d = self.getTaskResult(id, block=True)
            dList.append(d)
        d = DeferredList(dList, consumeErrors=1)
        d.addCallbacks(lambda r: None)
        return d
    
    def spin(self):
        return defer.succeed(self.distributeTasks())
    
    #---------------------------------------------------------------------------
    # Queue methods
    #---------------------------------------------------------------------------
    
    def _doAbort(self, taskID):
        """Helper function for aborting a pending task."""
        log.msg("Task #%i Aborted"%taskID)
        result = failure.Failure(error.TaskAborted())
        self._finishTask(taskID, result)
        if taskID in self.abortPending:
            self.abortPending.remove(taskID)
    
    def _finishTask(self, taskID, result):
        dlist = self.deferredResults.pop(taskID)
        result.taskID = taskID   # The TaskResult should save the taskID
        self.finishedResults[taskID] = result
        for d in dlist:
            d.callback(result)
    
    def distributeTasks(self):
        """Distribute tasks while self.scheduler has things to do."""
        log.msg("distributing Tasks")
        worker, task = self.scheduler.schedule()
        if not worker and not task:
            if self.idleLater and self.idleLater.called:# we are inside failIdle
                self.idleLater = None
            else:
                self.checkIdle()
            return False
        # else something to do:
        while worker and task:
            # get worker and task
            # add to pending
            self.pendingTasks[worker.workerID] = task
            # run/link callbacks
            d = worker.run(task)
            log.msg("running task #%i on worker %i" %(task.taskID, worker.workerID))
            d.addBoth(self.taskCompleted, task.taskID, worker.workerID)
            worker, task = self.scheduler.schedule()
        # check for idle timeout:
        self.checkIdle()
        return True
    
    def checkIdle(self):
        if self.idleLater and not self.idleLater.called:
            self.idleLater.cancel()
        if self.scheduler.ntasks and self.workers and \
                    self.scheduler.nworkers == len(self.workers):
            self.idleLater = reactor.callLater(self.timeout, self.failIdle)
        else:
            self.idleLater = None
    
    def failIdle(self):
        if not self.distributeTasks():
            while self.scheduler.ntasks:
                t = self.scheduler.popTask()
                msg = "Task %i failed to execute due to unmet dependencies"%t.taskID
                msg += " for %i seconds"%self.timeout
                log.msg("Task %i Aborted by timeout"%t.taskID)
                f = failure.Failure(error.TaskTimeout(msg))
                self._finishTask(t.taskID, f)
        self.idleLater = None
                
    
    def taskCompleted(self, result, taskID, workerID):
        """This is the err/callback for a completed task."""
        try:
            task = self.pendingTasks.pop(workerID)
        except:
            # this should not happen
            log.msg("tried to pop bad pending task#%i from worker #%i"%(taskID, workerID))
            log.msg("result: %r"%result)
            log.msg("pending tasks:%s"%self.pendingTasks)
            return
        
        # Check if aborted while pending
        aborted = False
        if taskID in self.abortPending:
            self._doAbort(taskID)
            aborted = True
        
        if not aborted:
            if result.failure is not None and isinstance(result.failure, failure.Failure): # we failed
                log.msg("Task #%i failed on worker %i"% (taskID, workerID))
                if task.retries > 0: # resubmit
                    task.retries -= 1
                    self.scheduler.addTask(task)
                    s = "resubmitting task #%i, %i retries remaining" %(taskID, task.retries)
                    log.msg(s)
                    self.distributeTasks()
                elif isinstance(task.recoveryTask, Task) and \
                                    task.recoveryTask.retries > -1:
                    # retries = -1 is to prevent infinite recoveryTask loop
                    task.retries = -1 
                    task.recoveryTask.taskID = taskID
                    task = task.recoveryTask
                    self.scheduler.addTask(task)
                    s = "recovering task #%i, %i retries remaining" %(taskID, task.retries)
                    log.msg(s)
                    self.distributeTasks()
                else: # done trying
                    self._finishTask(taskID, result)
                # wait a second before readmitting a worker that failed
                # it may have died, and not yet been unregistered
                reactor.callLater(self.failurePenalty, self.readmitWorker, workerID)
            else: # we succeeded
                log.msg("Task #%i completed "% taskID)
                self._finishTask(taskID, result)
                self.readmitWorker(workerID)
        else:# we aborted the task
            if result.failure is not None and isinstance(result.failure, failure.Failure): # it failed, penalize worker
                reactor.callLater(self.failurePenalty, self.readmitWorker, workerID)
            else:
                self.readmitWorker(workerID)
    
    def readmitWorker(self, workerID):
        """Readmit a worker to the scheduler.  
        
        This is outside `taskCompleted` because of the `failurePenalty` being 
        implemented through `reactor.callLater`.
        """
        
        if workerID in self.workers.keys() and workerID not in self.pendingTasks.keys():
            self.scheduler.addWorker(self.workers[workerID])
            self.distributeTasks()
        
    
components.registerAdapter(TaskController, cs.IControllerBase, ITaskController)
