#!/usr/bin/env python
# encoding: utf-8


#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

from twisted.internet import defer, reactor
from ipython1.testutils.util import DeferredTestCase
from ipython1.kernel.controllerservice import ControllerService
from ipython1.kernel.multiengine import IMultiEngine
from ipython1.kernel.tests.multienginetest import (ISynchronousMultiEngineTestCase,
    IFullSynchronousMultiEngineTestCase)

from ipython1.kernel.multienginexmlrpc import IXMLRPCMultiEngineFactory
from ipython1.kernel.multienginexmlrpc import XMLRPCFullSynchronousMultiEngineClient
from ipython1.kernel import multiengine as me

class FullSynchronousMultiEngineTestCase(DeferredTestCase, IFullSynchronousMultiEngineTestCase):
    
    def setUp(self):
        self.servers = []
        self.clients = []
        self.services = []
        
        self.controller = ControllerService()
        self.controller.startService()
        self.imultiengine = IMultiEngine(self.controller)
        self.imultiengine_factory = IXMLRPCMultiEngineFactory(self.imultiengine)
        self.servers.append(reactor.listenTCP(10105, self.imultiengine_factory))
        self.multiengine = XMLRPCFullSynchronousMultiEngineClient(('localhost',10105))
        self.engines = []
    
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
