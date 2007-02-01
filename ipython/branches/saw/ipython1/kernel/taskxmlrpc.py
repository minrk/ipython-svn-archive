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

from ipython1.kernel import error, blockon
from ipython1.kernel.task import TaskController, ITaskController
# from ipython1.kernel.taskcontrollerclient import ConnectingTaskControllerClient

#-------------------------------------------------------------------------------
# The Controller side of things
#-------------------------------------------------------------------------------

class IXMLRPCTaskController(Interface):
    """XML-RPC interface to task controller.  

    See the documentation of ITaskController for documentation about the methods.
    """
            
    def xmlrpc_run(request, expression, resultName, binNS):
        """"""
    
    def xmlrpc_getTaskResult(request, taskID):
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
        self.pendingDeferreds = {}
        self.results = {}
        
    
    #---------------------------------------------------------------------------
    # Non interface methods
    #---------------------------------------------------------------------------
    
    def finishDeferred(self, r, key):
        if isinstance(r, failure.Failure):
            r.cleanFailure()
        self.results[key] = r
        try:
            del self.pendingDeferreds[key]
        except:
            pass
        return None
    
    def returnResults(self, taskID, key):
        bin = xmlrpc.Binary(pickle.dumps((taskID, key, self.results),2))
        self.results = {}
        return bin
    
    #---------------------------------------------------------------------------
    # ITaskController related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_run(self, request, expression, resultName='', 
                            binaryNS=xmlrpc.Binary(pickle.dumps({},2))):
        try:
            namespace = pickle.loads(binaryNS.data)
        except:
            taskID = -1
            d = defer.fail()
        else:
            taskID, d = self.taskController.run(expression, resultName, **namespace)
        key = hash(d)
        self.pendingDeferreds[key] = d.addBoth(self.finishDeferred, key)
        return self.returnResults(taskID, key)
    
    def xmlrpc_getTaskResult(self, request, taskID):
        d = self.taskController.getTaskResult(taskID)
        key = hash(d)
        self.pendingDeferreds[key] = d.addBoth(self.finishDeferred, key)
        return self.returnResults(taskID, key)

    #---------------------------------------------------------------------------
    # IConnectingTaskController related methods
    #---------------------------------------------------------------------------
    
    def xmlrpc_blockOn(self, request, key):
        if not self.results.has_key(key) and self.pendingDeferreds.has_key(key):
            blockon.blockOn(self.pendingDeferreds[key])
        return self.returnResults(-1,-1)
    

components.registerAdapter(XMLRPCTaskControllerFromTaskController,
            TaskController, IXMLRPCTaskController)


class IXMLRPCTaskControllerFactory(Interface):
    pass
    
    
def XMLRPCServerFactoryFromTaskController(taskController):
    """Adapt a TaskController to a XMLRPCServerFactory."""
    s = server.Site(IXMLRPCTaskController(taskController))
    return channel.HTTPFactory(s)
    
    
components.registerAdapter(XMLRPCServerFactoryFromTaskController,
            TaskController, IXMLRPCTaskControllerFactory)
        

#-------------------------------------------------------------------------------
# The Client side of things
#-------------------------------------------------------------------------------

class XMLRPCTaskControllerClient(object):
    """XMLRPC based TaskController client that implements ITaskController.
    
    """
    
    implements(ITaskController)
    
    def __init__(self, server):
        self.server = server
        self.pendingDeferreds = {}
        
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
            self.fireCallbacks(results)
        return (taskID, key, results)
    
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
                (_, __, results) = self.handleReturn(self.server.blockOn(k))
                return blockon.blockOn(v)
    
    #---------------------------------------------------------------------------
    # ITaskController related methods
    #---------------------------------------------------------------------------
        
    def run(self, expression, resultName='', namespace={}):
        """run @expression as a task, in a namespace initialized to @namespace,
        wherein the desired result is stored in @resultName.  If @resultName 
        is not specified, None will be stored as the result.
        
        Returns a tuple of (taskID, deferred), where taskID is the ID of 
        the task associated with this call, and deferred is a deferred to 
        the result of the task."""
        bns = xmlrpc.Binary(pickle.dumps(namespace,2))
        (taskID, key, results) = self.handleReturn(self.server.run(expression, resultName, bns))
        self.pendingDeferreds[key] = d = defer.Deferred()
        
        return (taskID, d)
    
    def getTaskResult(self, taskID):
        """get the result of a task by its id.  This relinks your deferred
        to the one returned by run."""
        (taskID, key, results) = self.handleReturn(
            self.server.getTaskResult(taskID))
        self.pendingDeferreds[key] = d = defer.Deferred()
        self.fireCallbacks(results)
        return d
        

components.registerAdapter(XMLRPCTaskControllerClient, 
        xmlrpclib.ServerProxy, ITaskController)
    
    
#-------------------------------------------------------------------------------
# The XMLRPC version of ConnectingTaskControllerClient
#-------------------------------------------------------------------------------

class XMLRPCConnectingTaskClient(object):
    """XML-RPC version of the Connecting TaskControllerClient"""
    
    def __init__(self, addr):
        self.addr = addr
        self.taskcontroller = None
        self.block = False
        self.connected = False
                
    def _blockOrNot(self, d):
        if self.block:
            return self.blockOn(d)
        else:
            return d
    
    def connect(self):
        if not self.connected:
            addr = 'http://%s:%s/'%self.addr
            print "Connecting to ", addr
            self.taskcontroller = ITaskController(xmlrpclib.Server(addr))
            self.connected = True
    
    def disconnect(self):
        if self.connected:
            print "Disconnecting from ", self.addr
            del self.taskcontroller
            self.taskcontroller = None
            self.connected = False
    
    def run(self, expression, resultName='', namespace = {}, block=True):
        self.connect()
        (taskID, d) = self.taskcontroller.run(expression, resultName, namespace)
        return taskID, self._blockOrNot(d)
    
    def getTaskResult(self, taskID):
        self.connect()
        return self._blockOrNot(self.taskcontroller.getTaskResult(taskID))
    
    def blockOn(self, d):
        self.taskcontroller.blockOn(d)
        return blockon.blockOn(d)
    
