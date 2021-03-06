# encoding: utf-8
# -*- test-case-name: ipython1.test.test_taskcontrollerxmlrpc -*-
"""A PB interface to a TaskController.

This class lets PB clients talk to the TaskController
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

from zope.interface import Interface, implements
from twisted.internet import defer, reactor
from twisted.spread import pb
from twisted.python import components, failure

from ipython1.kernel import blockon, task, taskclient

#-------------------------------------------------------------------------------
# The Controller side of things
#-------------------------------------------------------------------------------

class IPBTaskController(Interface):
    """PB interface to task controller.  

    See the documentation of task.ITaskController for documentation about the methods.
    """
    def remote_getClientID():
        """gets a client id"""
    
    def remote_run(pTask):
        """see task.ITaskController"""
    
    def remote_getTaskResult(taskID):
        """see task.ITaskController"""
    
class PBTaskControllerFromTaskController(pb.Root):
    """PB attachmeot for controller.
    
    See IPBTaskController and task.ITaskController (and its children) for documentation. 
    """
    implements(IPBTaskController)
    
    def __init__(self, taskController):
        self.taskController = taskController
    
    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------
    
    def packageSuccess(self, r):
        return pickle.dumps(r, 2)
    
    def packageFailure(self, f):
        f.cleanFailure()
        pString = pickle.dumps(f, 2)
        return 'FAILURE:' + pString
    
    #---------------------------------------------------------------------------
    # task.ITaskController related methods
    #---------------------------------------------------------------------------
    
    def remote_run(self, pTask):
        try:
            task = pickle.loads(pTask)
        except:
            taskID = -1
            d = defer.fail()
        else:
            tr = self.taskController.run(task)
            # tr.result.addErrback(lambda _:None)# errors are handled elsewhere
            return tr.taskID
    
    def remote_getTaskResult(self, taskID):
        tr = self.taskController.getTaskResult(taskID)
        return tr.result.addCallback(self.packageSuccess).addErrback(self.packageFailure)
    

components.registerAdapter(PBTaskControllerFromTaskController,
            task.TaskController, IPBTaskController)


class IPBTaskControllerFactory(Interface):
    pass
    
def PBServerFactoryFromTaskController(taskController):
    """Adapt a TaskController to a PBServerFactory."""
    return pb.PBServerFactory(IPBTaskController(taskController))
    
    
components.registerAdapter(PBServerFactoryFromTaskController,
            task.TaskController, IPBTaskControllerFactory)
        

#-------------------------------------------------------------------------------
# The Client side of things
#-------------------------------------------------------------------------------

class PBTaskControllerClient(object):
    """PB based TaskController client that implements task.ITaskController.
    
    """
    
    implements(task.ITaskController)
    
    def __init__(self, reference):
        self.reference = reference
        self.callRemote = reference.callRemote
        
    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------
        
    def checkReturnForFailure(self, r):
        """See if a returned value is a pickled Failure object.
        
        To distinguish between general pickled objects and pickled Failures, the
        other side should prepend the string FAILURE: to any pickled Failure.
        """
        if isinstance(r, str):
            if r.startswith('FAILURE:'):
                r = r[8:]
            try: 
                result = pickle.loads(r)
            except pickle.PickleError:
                return failure.Failure( \
                    FailureUnpickleable("Could not unpickle failure."))
            else:
                return result
        
    #---------------------------------------------------------------------------
    # task.ITaskController related methods
    #---------------------------------------------------------------------------
        
    def run(self, task):
        """run a task, on the TaskController.  Returns a TaskResult object.
        """
        pTask = pickle.dumps(task,2)
        taskID = blockon.blockOn(self.callRemote('run', pTask))
        return self.getTaskResult(taskID)
    
    def getTaskResult(self, taskID):
        """get the result of a task by its id.  This relinks your deferred
        to the one returned by run.  Returns a TaskResult object"""
        d = self.callRemote('getTaskResult', taskID)
        return task.TaskResult(taskID, d.addCallback(self.checkReturnForFailure))
    

components.registerAdapter(PBTaskControllerClient, 
        pb.RemoteReference, task.ITaskController)
    
    
#-------------------------------------------------------------------------------
# The PB version of ConnectingTaskControllerClient
#-------------------------------------------------------------------------------

class PBConnectingTaskClient(taskclient.ConnectingTaskClient):
    """PB version of the Connecting TaskControllerClient"""
    
    def connect(self):
        """connect to TaskController"""
        if not self.connected:
            print "Connecting to ", self.addr
            self.factory = pb.PBClientFactory()
            d = self.factory.getRootObject()
            d.addCallback(self._gotRoot)
            reactor.connectTCP(self.addr[0], self.addr[1], self.factory)
            return blockon.blockOn(d)
    
    def disconnect(self):
        self.factory.disconnect()
        for i in range(10):
            reactor.iterate(0.1)
    
    def handleDisconnect(self, thingy):
        print "Disconnecting from ", self.addr
        self.connected = False
        self.taskcontroller = None
        self.factory = None
    
    def _gotRoot(self, rootObj):
        self.taskcontroller = task.ITaskController(rootObj)
        self.connected = True
        self.taskcontroller.reference.notifyOnDisconnect(self.handleDisconnect)