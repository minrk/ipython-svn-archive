# encoding: utf-8
# -*- test-case-name: ipython1.kernel.test.test_taskcontrollerxmlrpc -*-
"""An XML-RPC interface to a TaskController.

This class lets XML-RPC clients talk to a TaskController.
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

import cPickle as pickle
import xmlrpclib

from zope.interface import Interface, implements
from twisted.internet import defer
from twisted.python import components, failure
from twisted.web import xmlrpc as webxmlrpc

from ipython1.external.twisted.web2 import xmlrpc, server, channel

from ipython1.kernel import error, task as Task, taskclient
from ipython1.kernel.xmlrpcutil import Transport

#-------------------------------------------------------------------------------
# The Controller side of things
#-------------------------------------------------------------------------------

# This is used by twisted.web2 to determine the timeout between different 
# requests by a single client.
BETWEEN_REQUESTS_TIMEOUT = 15*60


class IXMLRPCTaskController(Interface):
    """XML-RPC interface to task controller.
        
    See the documentation of ITaskController for documentation about the methods.
    """
    def xmlrpc_run(request, binTask):
        """"""
    
    def xmlrpc_abort(request, taskid):
        """"""
        
    def xmlrpc_get_task_result(request, taskid, block=False):
        """"""
        
    def xmlrpc_barrier(request, taskids):
        """"""
    
    def xmlrpc_spin(request):
        """"""
    

class XMLRPCTaskControllerFromTaskController(xmlrpc.XMLRPC):
    """XML-RPC attachmeot for controller.
        
    See IXMLRPCTaskController and ITaskController (and its children) for documentation. 
    """
    implements(IXMLRPCTaskController)
    
    addSlash = True
    
    def __init__(self, taskController):
        xmlrpc.XMLRPC.__init__(self)
        self.taskController = taskController
    
    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------
    
    def packageFailure(self, f):
        f.cleanFailure()
        return self.packageSuccess(f)
    
    def packageSuccess(self, obj):
        # print 'returning: ',obj
        serial = pickle.dumps(obj, 2)
        return xmlrpc.Binary(serial)
    
    #---------------------------------------------------------------------------
    # ITaskController related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_run(self, request, binTask):
        try:
            task = pickle.loads(binTask.data)
        except:
            d = defer.fail(pickle.UnpickleableError("Could not unmarshal task"))
        else:
            d = self.taskController.run(task)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d
    
    def xmlrpc_abort(self, request, taskid):
        d = self.taskController.abort(taskid)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d
        
    def xmlrpc_get_task_result(self, request, taskid, block=False):
        d = self.taskController.get_task_result(taskid, block)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d

    def xmlrpc_barrier(self, request, taskids):
        d = self.taskController.barrier(taskids)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d        
    
    def xmlrpc_spin(self, request):
        d = self.taskController.spin()
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d        

components.registerAdapter(XMLRPCTaskControllerFromTaskController,
            Task.TaskController, IXMLRPCTaskController)


class IXMLRPCTaskControllerFactory(Interface):
    pass

def XMLRPCServerFactoryFromTaskController(taskController):
    """Adapt a TaskController to a XMLRPCServerFactory."""
    s = server.Site(IXMLRPCTaskController(taskController))
    return channel.HTTPFactory(s, betweenRequestsTimeOut=BETWEEN_REQUESTS_TIMEOUT)


components.registerAdapter(XMLRPCServerFactoryFromTaskController,
            Task.TaskController, IXMLRPCTaskControllerFactory)
        

#-------------------------------------------------------------------------------
# The Client side of things
#-------------------------------------------------------------------------------

class IXMLRPCTaskClient(Interface):
    pass

class XMLRPCTaskClient(object):
    """XML-RPC based TaskController client that implements ITaskController.
        
    :Parameters:
        addr : (ip, port)
            The ip (str) and port (int) tuple of the `TaskController`.  
    """
    implements(Task.ITaskController, IXMLRPCTaskClient)
        
    def __init__(self, addr):
        self.addr = addr
        self.url = 'http://%s:%s/' % self.addr
        self._proxy = webxmlrpc.Proxy(self.url)
    
    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------
        
    def unpackage(self, r):
        return pickle.loads(r.data)
      
    #---------------------------------------------------------------------------
    # ITaskController related methods
    #---------------------------------------------------------------------------
    def run(self, task):
        """Run a task on the `TaskController`.
                
        :Parameters:
            task : a `Task` object
        
        The Task object is created using the following signature:
        
        Task(expression, pull=None, push={}, clear_before=False, 
            clear_after=False, retries=0, **options):)

        The meaning of the arguments is as follows:

        :Task Parameters:
            expression : str
                A str that is valid python code that is the task.
            pull : str or list of str 
                The names of objects to be pulled as results.
            push : dict
                A dict of objects to be pushed into the engines namespace before
                execution of the expression.
            clear_before : boolean
                Should the engine's namespace be cleared before the task is run.
                Default=False.
            clear_after : boolean 
                Should the engine's namespace be cleared after the task is run.
                Default=False.
            retries : int
                The number of times to resumbit the task if it fails.  Default=0.
            options : dict
                Any other keyword options for more elaborate uses of tasks
            
        :Returns: The int taskid of the submitted task.  Pass this to 
            `get_task_result` to get the `TaskResult` object.
        """
        assert isinstance(task, Task.Task), "task must be a Task object!"
        binTask = xmlrpc.Binary(pickle.dumps(task,2))
        d = self._proxy.callRemote('run', binTask)
        d.addCallback(self.unpackage)
        return d
    
    def get_task_result(self, taskid, block=False):
        """The task result by taskid.
        
        :Parameters:
            taskid : int
                The taskid of the task to be retrieved.
            block : boolean
                Should I block until the task is done?
        
        :Returns: A `TaskResult` object that encapsulates the task result.
        """
        d = self._proxy.callRemote('get_task_result', taskid, block)
        d.addCallback(self.unpackage)
        return d 
    
    def abort(self, taskid):
        """Abort a task by taskid.
        
        :Parameters:
            taskid : int
                The taskid of the task to be aborted.
            block : boolean
                Should I block until the task is aborted.        
        """
        d = self._proxy.callRemote('abort', taskid)
        d.addCallback(self.unpackage)
        return d 
        
    def barrier(self, taskids):
        """Block until all tasks are completed.
        
        :Parameters:
            taskids : list, tuple
                A sequence of taskids to block on.
        """
        d = self._proxy.callRemote('barrier', taskids)
        d.addCallback(self.unpackage)
        return d 
    
    def spin(self):
        """touch the scheduler, to resume scheduling without submitting
        a task.
        """
        d = self._proxy.callRemote('spin')
        d.addCallback(self.unpackage)
        return d



