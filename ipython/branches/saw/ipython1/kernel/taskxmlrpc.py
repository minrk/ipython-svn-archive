# encoding: utf-8
# -*- test-case-name: ipython1.test.test_taskcontrollerxmlrpc -*-
"""An XML-RPC interface to a TaskController.
This class lets XMLRPC clients talk to the ControllerService.  The main difficulty
is that XMLRPC doesn't allow arbitrary objects to be sent over the wire - only
basic Python types.  To get around this we simple pickle more complex objects
on boths side of the wire.  That is the main thing these classes have to 
manage.
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

from ipython1.external.twisted.web2 import xmlrpc, server, channel

from ipython1.kernel import error, task as Task, taskclient
from ipython1.kernel.multiengineclient import PendingResult
from ipython1.kernel.xmlrpcutil import Transport

#-------------------------------------------------------------------------------
# The Controller side of things
#-------------------------------------------------------------------------------

BETWEEN_REQUESTS_TIMEOUT = 15*60


class IXMLRPCTaskController(Interface):
    """XML-RPC interface to task controller.
        
    See the documentation of ITaskController for documentation about the methods.
    """
    def xmlrpc_run(request, clientID, binTask, block):
        """see ITaskController"""
    
    #---------------------------------------------------------------------------
    # Pending Deferred related methods
    #---------------------------------------------------------------------------            
    def xmlrpc_registerClient(request):
        """"""
    
    def xmlrpc_unregisterClient(request, clientID):
        """"""
    
    def xmlrpc_getPendingResult(request, clientID, resultID):
        """"""
    
    def xmlrpc_getAllPendingResults(self, clientID):
        """"""
    
class XMLRPCTaskControllerFromTaskController(xmlrpc.XMLRPC):
    """XML-RPC attachmeot for controller.
        
    See IXMLRPCTaskController and ITaskController (and its children) for documentation. 
    """
    implements(IXMLRPCTaskController)
    
    addSlash = True
    
    def __init__(self, taskController):
        xmlrpc.XMLRPC.__init__(self)
        self.staskcontroller = Task.ISynchronousTaskController(taskController)
        self.pendingDeferreds = {}
        self.results = {}
        self.clientIndex = 0
    
    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------
    
    def packageFailure(self, f):
        f.cleanFailure()
        return self.packageSuccess(f)
    
    def packageSuccess(self, obj):
        serial = pickle.dumps(obj, 2)
        return xmlrpc.Binary(serial)
    
    #---------------------------------------------------------------------------
    # ITaskController related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_run(self, request, clientID, block, binTask):
        try:
            task = pickle.loads(binTask.data)
        except:
            d = defer.fail(pickle.UnPickleableError("Could not unmarshal task"))
        else:
            d = self.staskcontroller.run(clientID, block, task)
            # print tr
            # print block
            # if block:
            #     d.addCallback(self._runCallback, clientID, block)
            # taskID = task.taskID
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d
    
    # def _runCallback(self, taskID, clientID, block):
    #     return self.getTaskResult(clientID, taskID, block)
        # d.addBoth(self.finishDeferred, clientID, key)
        # return self.returnResults(clientID, taskID, key)
    
    def xmlrpc_getTaskResult(self, request, clientID, block, taskID):
        d = self.staskcontroller.getTaskResult(clientID, block, taskID)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d
    
    #---------------------------------------------------------------------------
    # Pending Deferred related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_registerClient(self, request):
        """"""
        clientID = self.staskcontroller.registerClient()
        return clientID
    
    def xmlrpc_unregisterClient(self, request, clientID):
        """"""
        try:
            self.staskcontroller.unregisterClient(clientID)
        except error.InvalidClientID:
            f = failure.Failure()
            return self.packageFailure(f)
        else:
            return True
    
    def xmlrpc_getPendingResult(self, request, clientID, resultID, block):
        """"""
        d = self.staskcontroller.getPendingDeferred(clientID, resultID, block)
        d.addCallback(self.packageSuccess)
        d.addErrback(self.packageFailure)
        return d
    
    # xmlrpc_getTask
    def xmlrpc_getAllPendingResults(self, request, clientID):
        """"""    
        d = self.staskcontroller.getAllPendingDeferreds(clientID)
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
    return channel.HTTPFactory(s)


components.registerAdapter(XMLRPCServerFactoryFromTaskController,
            Task.TaskController, IXMLRPCTaskControllerFactory)
        

#-------------------------------------------------------------------------------
# The Client side of things
#-------------------------------------------------------------------------------

class XMLRPCTaskClient(object):
    """XMLRPC based TaskController client that implements ITaskController.
        
    """
    implements(Task.ITaskController)
    
    
    #---------------------------------------------------------------------------
    # Begin copy from XMLRPCMultiEngineClient
    # Should these methods be in a base XMLRPCClient class?
    #---------------------------------------------------------------------------
    
    def __init__(self, addr):
        self.addr = addr
        self.url = 'http://%s:%s/' % self.addr
        self.server = xmlrpclib.ServerProxy(self.url, transport=Transport(), 
            verbose=0)
        self.clientID = None
        self.block = True
    
    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------
        
    def _reallyBlock(self, block=None):
        if block is None:
            return self.block
        else:
            if block in (True, False):
                return block
            else:
                raise ValueError("block must be True or False")
    
    def _executeRemoteMethod(self, f, *args):
        try:
            rawResult = f(*args)
            result = self._unpackageResult(rawResult)
        except error.InvalidClientID:
            self._getClientID()
            rawResult = f(*args)
            result = self._unpackageResult(rawResult)
        return result
    
    def _unpackageResult(self, result):
        result = pickle.loads(result.data)
        return self._returnOrRaise(result)
    
    def _returnOrRaise(self, result):
        if isinstance(result, failure.Failure):
            result.raiseException()
        else:
            return result
    
    def _checkClientID(self):
        if self.clientID is None:
            self._getClientID()
    
    def _getClientID(self):
        clientID = self.server.registerClient()
        self.clientID = clientID
    
    #---------------------------------------------------------------------------
    # Pending results related methods
    #--------------------------------------------------------------------------- 
    
    def getPendingResult(self, resultID, block=True):
        self._checkClientID()
        return self._executeRemoteMethod(self.server.getPendingResult,
            self.clientID, resultID, block)
    
    def getAllPendingResults(self):
        self._checkClientID()
        result = self._executeRemoteMethod(self.server.getAllPendingResults, self.clientID)
        for r in result:
            if isinstance(r, failure.Failure):
                r.raiseException()
        if len(result) == 1:
            result = result[0]
        return result
    
    def barrier(self):
        self._checkClientID()
        result = self._executeRemoteMethod(self.server.getAllPendingResults, self.clientID)
        for r in result:
            if isinstance(r, failure.Failure):
                r.raiseException() 
    
    #---------------------------------------------------------------------------
    # end copy from multienginexmlrpc
    #---------------------------------------------------------------------------
    
    #---------------------------------------------------------------------------
    # ITaskController related methods
    #---------------------------------------------------------------------------
    def run(self, task, block=None):
        """run @expression as a task, in a namespace initialized to @namespace,
        wherein the desired result is stored in @resultName.  If @resultName 
        is not specified, None will be stored as the result.
            
        Returns a tuple of (taskID, deferred), where taskID is the ID of 
        the task associated with this call, and deferred is a deferred to 
        the result of the task."""
        self._checkClientID()
        assert isinstance(task, Task.Task), "task must be a Task object!"
        localBlock = self._reallyBlock(block)
        binTask = xmlrpc.Binary(pickle.dumps(task,2))
        result = self._executeRemoteMethod(self.server.run, self.clientID, localBlock, binTask)
        # if not localBlock:
        #     result = PendingResult(self, result)
        return result
    
    def getTaskResult(self, taskID, block=None):
        """"""
        self._checkClientID()
        localBlock = self._reallyBlock(block)
        result = self._executeRemoteMethod(self.server.getTaskResult, self.clientID, localBlock, taskID)
        if not localBlock:
            result = PendingResult(self, result)
        return result
    

components.registerAdapter(XMLRPCTaskClient, 
        xmlrpclib.ServerProxy, Task.ITaskController)
    

class XMLRPCInteractiveTaskClient(XMLRPCTaskClient, taskclient.InteractiveTaskClient):
    pass

# #-------------------------------------------------------------------------------
# # The XMLRPC version of ConnectingTaskControllerClient
# #-------------------------------------------------------------------------------
# 
# class XMLRPCConnectingTaskClient(taskclient.ConnectingTaskClient):
#     """XML-RPC version of the Connecting TaskControllerClient"""
#     
#     def connect(self):
#         if not self.connected:
#             addr = 'http://%s:%s/'%self.addr
#             print "Connecting to ", addr
#             self.taskcontroller = XMLRPCTaskControllerClient(xmlrpclib.Server(addr))
#             self.connected = True
#     
#     def disconnect(self):
#         if self.connected:
#             print "Disconnecting from ", self.addr
#             del self.taskcontroller
#             self.taskcontroller = None
#             self.connected = False
#     
