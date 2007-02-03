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

from ipython1.kernel import error, blockon, task, taskclient

#-------------------------------------------------------------------------------
# The Controller side of things
#-------------------------------------------------------------------------------

class IXMLRPCTaskController(Interface):
    """XML-RPC interface to task controller.  

    See the documentation of ITaskController for documentation about the methods.
    """
    def xmlrpc_getClientID(request):
        """gets a client id"""
    
    def xmlrpc_run(request, clientID, binTask):
        """see ITaskController"""
    
    def xmlrpc_getTaskResult(request, clientID, taskID):
        """see ITaskController"""
    
    def xmlrpc_blockOn(request, clientID, key):
        """see IConnectingTaskController"""
        
class XMLRPCTaskControllerFromTaskController(xmlrpc.XMLRPC):
    """XML-RPC attachmeot for controller.
    
    See IXMLRPCTaskController and ITaskController (and its children) for documentation. 
    """
    implements(IXMLRPCTaskController)
    
    addSlash = True
    
    def __init__(self, taskController):
        xmlrpc.XMLRPC.__init__(self)
        self.taskController = taskController
        self.pendingDeferreds = {}
        self.results = {}
        self.clientIndex = 0
    
    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------
    
    def finishDeferred(self, r, clientID, key):
        if isinstance(r, failure.Failure):
            r.cleanFailure()
        if not self.results.has_key(clientID):
            self.results[clientID] = {}
        self.results[clientID][key] = r
        try:
            del self.pendingDeferreds[key]
        except:
            pass
    
    def returnResults(self, clientID, taskID, key):
        if not self.results.has_key(clientID):
            self.results[clientID] = {}
        bin = xmlrpc.Binary(pickle.dumps((taskID, key, self.results[clientID]),2))
        self.results[clientID] = {}
        return bin
    
    #---------------------------------------------------------------------------
    # IXMLRPCTaskController related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_getClientID(self, request):
        clientID = self.clientIndex
        self.clientIndex += 1
        return clientID
    
    #---------------------------------------------------------------------------
    # ITaskController related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_run(self, request, clientID, binTask):
        try:
            task = pickle.loads(binTask.data)
        except:
            taskID = -1
            d = defer.fail()
        else:
            d = self.taskController.run(task)
            taskID = task.taskID
        key = hash(d)
        self.pendingDeferreds[key] = d
        d.addBoth(self.finishDeferred, clientID, key)
        return self.returnResults(clientID, taskID, key)
    
    def xmlrpc_getTaskResult(self, request, clientID, taskID):
        d = self.taskController.getTaskResult(taskID)
        key = hash(d)
        self.pendingDeferreds[key] = d
        d.addBoth(self.finishDeferred, clientID, key)
        return self.returnResults(clientID, taskID, key)

    #---------------------------------------------------------------------------
    # IConnectingTaskController related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_blockOn(self, request, clientID, key):
        if self.pendingDeferreds.has_key(key):
            blockon.blockOn(self.pendingDeferreds[key])
        return self.returnResults(clientID,-1,-1)
    

components.registerAdapter(XMLRPCTaskControllerFromTaskController,
            task.TaskController, IXMLRPCTaskController)


class IXMLRPCTaskControllerFactory(Interface):
    pass
    
def XMLRPCServerFactoryFromTaskController(taskController):
    """Adapt a TaskController to a XMLRPCServerFactory."""
    s = server.Site(IXMLRPCTaskController(taskController))
    return channel.HTTPFactory(s)
    
    
components.registerAdapter(XMLRPCServerFactoryFromTaskController,
            task.TaskController, IXMLRPCTaskControllerFactory)
        

#-------------------------------------------------------------------------------
# The Client side of things
#-------------------------------------------------------------------------------

class XMLRPCTaskControllerClient(object):
    """XMLRPC based TaskController client that implements ITaskController.
    
    """
    
    implements(task.ITaskController)
    
    def __init__(self, server):
        self.server = server
        self.pendingDeferreds = {}
        self.clientID = self.server.getClientID()
        
    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------
        
    def handleReturn(self, r):
        """Remote methods should either return a pickled object or a pickled
        failure object prefixed with "FAILURE:"
        """
        try:
            (taskID, key, results) = pickle.loads(r.data)
        except pickle.PickleError:
            raise error.KernelError("Could not unpickle returned object.")
        if key == -1:# not linked through
            d = defer.succeed(None)
        else:
            self.pendingDeferreds[key] = d = defer.Deferred()
        self.fireCallbacks(results)
        return (taskID, key, d)
    
    def fireCallbacks(self, results):
        for key , result in results.iteritems():
            if self.pendingDeferreds.has_key(key):
                self.pendingDeferreds[key].callback(result)
                del self.pendingDeferreds[key]
    
    
    #---------------------------------------------------------------------------
    # IXMLRPCTaskControllerClient
    #---------------------------------------------------------------------------
    
    def blockOn(self, d):
        for k,v in self.pendingDeferreds.iteritems():
            if d is v:
                self.handleReturn(self.server.blockOn(self.clientID, k))
                return blockon.blockOn(d)
    
    #---------------------------------------------------------------------------
    # ITaskController related methods
    #---------------------------------------------------------------------------
        
    def run(self, task):
        """run @expression as a task, in a namespace initialized to @namespace,
        wherein the desired result is stored in @resultName.  If @resultName 
        is not specified, None will be stored as the result.
        
        Returns a tuple of (taskID, deferred), where taskID is the ID of 
        the task associated with this call, and deferred is a deferred to 
        the result of the task."""
        binTask = xmlrpc.Binary(pickle.dumps(task,2))
        (taskID, key, d) = self.handleReturn(
                self.server.run(self.clientID, binTask))
        task.taskID = taskID
        task.result = d
        return d
    
    def getTaskResult(self, taskID):
        """get the result of a task by its id.  This relinks your deferred
        to the one returned by run."""
        (taskID, key, d) = self.handleReturn(
            self.server.getTaskResult(self.clientID, taskID))
        return d
        

components.registerAdapter(XMLRPCTaskControllerClient, 
        xmlrpclib.ServerProxy, task.ITaskController)
    
    
#-------------------------------------------------------------------------------
# The XMLRPC version of ConnectingTaskControllerClient
#-------------------------------------------------------------------------------

class XMLRPCConnectingTaskClient(taskclient.ConnectingTaskClient):
    """XML-RPC version of the Connecting TaskControllerClient"""
    
    def connect(self):
        if not self.connected:
            addr = 'http://%s:%s/'%self.addr
            print "Connecting to ", addr
            self.taskcontroller = XMLRPCTaskControllerClient(xmlrpclib.Server(addr))
            self.connected = True
    
    def disconnect(self):
        if self.connected:
            print "Disconnecting from ", self.addr
            del self.taskcontroller
            self.taskcontroller = None
            self.connected = False
    
