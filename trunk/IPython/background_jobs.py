# -*- coding: utf-8 -*-
"""Manage background (threaded) jobs conveniently from an interactive shell.

This module provides a BackgroundJobManager class.  This is the main class
meant for public usage, it implements an object which can create and manage
new background jobs.

It also provides the actual job classes managed by these BackgroundJobManager
objects, see their docstrings below.


This system was inspired by discussions with B. Granger and the
BackgroundCommand class described in the book Python Scripting for
Computational Science, by H. P. Langtangen:
http://folk.uio.no/hpl/scripting

$Id$
"""

#*****************************************************************************
#       Copyright (C) 2005 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from IPython import Release
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = Release.license

# Code begins
import threading

from IPython.ultraTB import AutoFormattedTB
from IPython.genutils import warn,error

# declares Python 2.2 compatibility symbols:
try:
    basestring
except NameError:
    import types
    basestring = (types.StringType, types.UnicodeType)
    True = 1==1
    False = 1==0

class BackgroundJobManager:
    """Class to manage a pool of backgrounded threaded jobs.

    Below, we assume that 'jobs' is a BackgroundJobManager instance.  To add a
    new job, use job.new() (docstring below).

    To query the current status of all managed jobs, use jobs.status(), or
    simply call the jobs object directly: jobs().  The __call__ method
    forwards the call to the status() method, to mimic conveniently the use of
    the Unix 'jobs' command if your job manager is called 'jobs'.

    A job manager implements __getitem__, to allow job retrieval via a simple
    [] syntax:

      jobs[5] -> returns job object #5

    To read the result of job #5 and store it into variable 'foo', once it
    completes, use

      foo = jobs[5].result

    To flush the lists of finished jobs (successfully completed or dead), use
    jobs.flush_finished().
    """

    def __init__(self):
        # Lists for job management
        self.run_jobs  = []
        self.comp_jobs = []
        self.dead_jobs = []
        # A dict of all jobs, so users can easily access any of them
        self.all_jobs = {}
        # For reporting
        self.comp_report = []
        self.dead_report = []
        # Store status codes locally for fast lookups
        self.s_created   = BackgroundJobBase.stat_created_c
        self.s_running   = BackgroundJobBase.stat_running_c
        self.s_completed = BackgroundJobBase.stat_completed_c
        self.s_dead      = BackgroundJobBase.stat_dead_c

    def new(self,func_or_exp,*args,**kwargs):
        """Add a new background job and start it in a separate thread.

        It is important to note that all threads running share the standard
        output.  Thus, if your background jobs generate output, it will come
        out on top of whatever you are currently writing.  For this reason,
        background jobs are best used with silent functions which simply
        return their output.

        There are two types of jobs which can be created:

        1. Jobs based on expressions which can be passed to an eval() call.
        The expression must be given as a string.  For example:

          job_manager.new('myfunc(x,y,z=1)')

        The given expression is passed to eval().

        2. Jobs given a function object, optionally passing additional
        positional and keyword arguments:

          job_manager.new(myfunc,x,y,z=1)

        The function is called with the given arguments.

        In both cases, the result is stored in the job.result field of the
        background job object.
        """
        
        if callable(func_or_exp):
            job = BackgroundJobFunc(func_or_exp,*args,**kwargs)
        elif isinstance(func_or_exp,basestring):
            job = BackgroundJobExpr(func_or_exp)
        else:
            raise
        job.num = len(self.all_jobs)
        self.run_jobs.append(job)
        self.all_jobs[job.num] = job
        print 'Starting job # %s in a separate thread.' % job.num
        job.start()
        return job

    def __getitem__(self,key):
        return self.all_jobs[key]

    def __call__(self):
        """An alias to self.status(),

        This allows you to simply call a job manager instance much like the
        Unix jobs shell command."""
        return self.status()

    def _update_status(self):
        """Update the status of the job lists.

        This method moves finished jobs to one of two lists:
          - self.comp_jobs: jobs which completed successfully
          - self.dead_jobs: jobs which finished but died.

        It also copies those jobs to corresponding _report lists.  These lists
        are used to report jobs completed/dead since the last update, and are
        then cleared by the reporting function after each call."""
        
        run,comp,dead = self.s_running,self.s_completed,self.s_dead
        run_jobs = self.run_jobs
        for num in range(len(run_jobs)):
            job  = run_jobs[num]
            stat = job.stat_code
            if stat == run:
                continue
            elif stat == comp:
                self.comp_jobs.append(job)
                self.comp_report.append(job)
                run_jobs[num] = False
            elif stat == dead:
                self.dead_jobs.append(job)
                self.dead_report.append(job)
                run_jobs[num] = False
        self.run_jobs = filter(None,self.run_jobs)

    def _group_report(self,group,name):
        """Report summary for a given job group.

        Return True if the group had any elements."""

        if group:
            print '%s jobs:' % name
            for job in group:
                print '%s : %s' % (job.num,job)
            print
            return True

    def _group_flush(self,group,name):
        """Flush a given job group

        Return True if the group had any elements."""

        njobs = len(group)
        if njobs:
            plural = {1:''}.setdefault(njobs,'s')
            print 'Flushing %s %s job%s.' % (njobs,name,plural)
            group[:] = []
            return True
        
    def _status_new(self):
        """Print the status of newly finished jobs.

        Return True if any new jobs are reported.

        This call resets its own state every time, so it only reports jobs
        which have finished since the last time it was called."""

        self._update_status()
        new_comp = self._group_report(self.comp_report,'Completed')
        new_dead = self._group_report(self.dead_report,
                                      'Dead, call job.traceback() for details')
        self.comp_report[:] = []
        self.dead_report[:] = []
        return new_comp or new_dead
                
    def status(self,verbose=0):
        """Print a status of all jobs currently being managed."""

        self._update_status()
        self._group_report(self.run_jobs,'Running')
        self._group_report(self.comp_jobs,'Completed')
        self._group_report(self.dead_jobs,'Dead')
        # Also flush the report queues
        self.comp_report[:] = []
        self.dead_report[:] = []

    def flush_finished(self):
        """Flush all jobs finished (completed and dead) from lists.

        Running jobs are never flushed.

        It first calls _status_new(), to update info. If any jobs have
        completed since the last _status_new() call, the flush operation
        aborts."""

        if self._status_new():
            error('New jobs completed since last '\
                  '_status_new(), aborting flush.')
            return
        fl_comp = self._group_flush(self.comp_jobs,'Completed')
        fl_dead = self._group_flush(self.dead_jobs,'Dead')
        if not (fl_comp or fl_dead):
            print 'No jobs to flush.'

class BackgroundJobBase(threading.Thread):
    """Base class to build BackgroundJob classes.

    The derived classes must implement:

    - Their own __init__, since the one here raises NotImplementedError.  This
    constructor must call self._init() at the end, to provide common
    initialization.

    - A strform attribute used in calls to __str__.

    - A call() method, which will make the actual execution call and must
    return a value to be held in the 'result' field of the job object.
    """

    # Class constants for status, in string and as numerical codes (when
    # updating jobs lists, we don't want to do string comparisons).  This will
    # be done at every user prompt, so it has to be as fast as possible
    stat_created   = 'Created'; stat_created_c = 0
    stat_running   = 'Running'; stat_running_c = 1
    stat_completed = 'Completed'; stat_completed_c = 2
    stat_dead      = 'Dead (Exception), call job.traceback() for details'
    stat_dead_c = -1

    def __init__(self):
        raise NotImplementedError, \
              "This class can not be instantiated directly."

    def _init(self):

        for attr in ['call','strform']:
            assert hasattr(self,attr), "Missing attribute <%s>" % attr
        
        # The num tag can be set by an external job manager
        self.num = None
      
        self.status    = BackgroundJobBase.stat_created
        self.stat_code = BackgroundJobBase.stat_created_c
        self.finished  = False
        self.result    = '<BackgroundJob has not completed>'
        # reuse the ipython traceback handler if we can get to it, otherwise
        # make a new one
        try:
            self._make_tb = __IPYTHON__.InteractiveTB.text
        except:
            self._make_tb = AutoFormattedTB(mode = 'Context',
                                           color_scheme='NoColor',
                                           tb_offset = 1).text
        # Hold a formatted traceback if one is generated.
        self._tb = None
        
        threading.Thread.__init__(self)

    def __str__(self):
        return self.strform

    def __repr__(self):
        return '<BackgroundJob: %s>' % self.strform

    def traceback(self):
        print self._tb
        
    def run(self):
        try:
            self.status    = BackgroundJobBase.stat_running
            self.stat_code = BackgroundJobBase.stat_running_c
            self.result    = self.call()
        except:
            self.status    = BackgroundJobBase.stat_dead
            self.stat_code = BackgroundJobBase.stat_dead_c
            self.finished  = None
            self.result    = ('<BackgroundJob died, call job.traceback()>')
            self._tb       = self._make_tb()
        else:
            self.status    = BackgroundJobBase.stat_completed
            self.stat_code = BackgroundJobBase.stat_completed_c
            self.finished  = True

class BackgroundJobExpr(BackgroundJobBase):
    """Evaluate an expression as a background job (uses a separate thread)."""

    def __init__(self,expression):
        """Create a new job from a string which can be fed to eval()."""

        assert isinstance(expression,basestring),\
               'expression must be a string'
        self.expression = self.strform = expression
        self._init()
        
    def call(self):
        return eval(self.expression)

class BackgroundJobFunc(BackgroundJobBase):
    """Run a function call as a background job (uses a separate thread)."""

    def __init__(self,func,*args,**kwargs):
        """Create a new job from a callable object.

        Any positional arguments and keyword args given to this constructor
        after the initial callable are passed directly to it."""

        assert callable(func),'first argument must be callable'
        
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        
        self.func = func
        self.args = args
        self.kwargs = kwargs
        # The string form will only include the function passed, because
        # generating string representations of the arguments is a potentially
        # _very_ expensive operation (e.g. with large arrays).
        self.strform = str(func)
        self._init()

    def call(self):
        return self.func(*self.args,**self.kwargs)


if __name__=='__main__':

    import time

    def sleepfunc(interval=2,*a,**kw):
        args = dict(interval=interval,
                    args=a,
                    kwargs=kw)
        time.sleep(interval)
        return args

    def diefunc(interval=2,*a,**kw):
        time.sleep(interval)
        die

    def printfunc(interval=1,reps=5):
        for n in range(reps):
            time.sleep(interval)
            print 'In the background...'

    jobs = BackgroundJobManager()
    # first job will have # 0
    jobs.new(sleepfunc,4)
    # This makes a job which will die
    jobs.new(diefunc,1)
    jobs.new('printfunc(1,3)')

    # after a while, you can get the traceback of a dead job.  Run the line
    # below again interactively until it prints a traceback (check the status
    # of the job):
    print jobs[1].status
    jobs[1].traceback()
    
    # Run this line again until the printed result changes
    print "The result of job #0 is:",jobs[0].result
