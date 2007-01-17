# encoding: utf-8
"""This file contains unittests for the enginepb.py module.
"""
__docformat__ = "restructuredtext en"
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import sys

from twisted.python import components, log
from twisted.internet import reactor, defer

import zope.interface as zi
from ipython1.kernel.controllerservice import IControllerBase
from ipython1.kernel import engineservice as es
from ipython1.test.util import DeferredTestCase
from ipython1.kernel.enginevanilla import \
    VanillaEngineServerFactoryFromControllerService, \
    VanillaEngineClientFactoryFromEngineService

from ipython1.test.engineservicetest import \
    IEngineCoreTestCase, \
    IEngineSerializedTestCase, \
    IEngineQueuedTestCase

defer.setDebugging(1)

class EngineVanillaTest(DeferredTestCase, 
                   IEngineCoreTestCase, 
                   IEngineSerializedTestCase,
                   IEngineQueuedTestCase):
        
    zi.implements(IControllerBase)
        
    def setUp(self):
        self.services = []
        self.clients = []
        self.servers = []
        
        # Start a server and append to self.servers
        self.sf = VanillaEngineServerFactoryFromControllerService(self)    
        self.servers.append(reactor.listenTCP(10201, self.sf))
        
        # Start an EngineService and append to services/client
        self.engines = es.EngineService()
        ef = VanillaEngineClientFactoryFromEngineService(self.engines)
        #starterDeferred = defer.Deferred()
        #def myNotifySetID():
        #    starterDeferred.callback(None)
        #ef.notifySetID = myNotifySetID

        client = reactor.connectTCP('127.0.0.1', 10201, ef)
        self.clients.append(client)
        self.services.append(self.engines)
        self.engines.startService()
        
        # Create and returna Deferred that will fire when self.registerEngine
        # is called.  By returning this deferred, the actual tests will not
        # be run until the client has connected and is registered.
        self.setUpDeferred = defer.Deferred()
        return self.setUpDeferred
        #return starterDeferred
        
    def tearDown(self):
        l = []
        for s in self.servers:
            d = s.stopListening()
            if d is not None:
                l.append(d)
        for c in self.clients:
            c.disconnect()
            del c
        dl = defer.DeferredList(l)
        return dl
    
    #---------------------------------------------------------------------------
    # Make me look like a basic controller
    #---------------------------------------------------------------------------
    
    MAX_MESSAGE_SIZE = 2*640*1024
    
    def registerEngine(self, remoteEngine, id):
        self.engine = remoteEngine
        self.engine.id = 0
        reactor.callLater(0, self.setUpDeferred.callback, None)
        return {'id': 0, 'MAX_MESSAGE_SIZE':self.MAX_MESSAGE_SIZE}
    
    def unregisterEngine(self, id):
        pass