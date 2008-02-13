#!/usr/bin/env python
# encoding: utf-8
__docformat__ = "restructuredtext en"


#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import time

from twisted.internet import defer, reactor

from ipython1.kernel import task, controllerservice as cs
import ipython1.kernel.multiengine as me
from ipython1.testutils.util import DeferredTestCase
from ipython1.kernel import taskxmlrpc
from ipython1.kernel import multienginexmlrpc as mexmlrpc
from ipython1.kernel.util import printer
from ipython1.kernel.tests.tasktest import ITaskControllerTestCase

#-------------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------------

class TaskTest(DeferredTestCase, ITaskControllerTestCase):
    
    def setUp(self):
        self.servers = []
        self.clients = []
        self.services = []
        self.engines = []
        
        self.controller = cs.ControllerService()
        self.controller.startService()
        
        self.imultiengine = me.IMultiEngine(self.controller)
        self.imultiengine_factory = mexmlrpc.IXMLRPCMultiEngineFactory(self.imultiengine)
        self.servers.append(reactor.listenTCP(10105, self.imultiengine_factory))
        self.multiengine = mexmlrpc.XMLRPCSynchronousMultiEngineClient(('localhost',10105))
        
        self.itc = task.ITaskController(self.controller)
        self.itc.failurePenalty = 0
        self.itc_factory = taskxmlrpc.IXMLRPCTaskControllerFactory(self.itc)
        self.servers.append(reactor.listenTCP(10113, self.itc_factory))
        self.tc = taskxmlrpc.XMLRPCTaskClient(('localhost',10113))
    
    def tearDown(self):
        l = []
        for s in self.servers:
            try:
                d = s.stopListening()
                if d is not None:
                    l.append(d)
            except:
                pass
        for c in self.clients:
            c.disconnect()
            del c
        dl = defer.DeferredList(l)
        self.controller.stopService()
        for e in self.engines:
            e.stopService()
        return dl
