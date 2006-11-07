# encoding: utf-8
"""This file contains unittests for the enginepb.py module.

Things that should be tested:
The methods of Controller Service:
 - registerEngine
 - unregisterEngine
 - execute/All
 - push/Serial/All
 - pull/Serial/All
 - getResult/All
 - status/All
 - reset/All
 - *kill/All - do not test this, it calls reactor.stop

"""

#*****************************************************************************
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from twisted.python import components, log
from twisted.internet import reactor, defer

defer.setDebugging(1)

import sys

from ipython1.core.shell import InteractiveShell
from ipython1.kernel import engineservice as es, enginevanilla as ev
from ipython1.test import util
from ipython1.test  import completeenginetest as cet

evsf = ev.VanillaEngineServerFactoryFromControllerService

#log.startLogging(sys.stdout)
class EngineVanillaTest(cet.CompleteEngineTestCase):
#class EnginePBTest(util.DeferredTestCase):
        
    def setUp(self):
        #start one controller and connect one engine
        self.services = []
        self.clients = []
        self.servers = []
        
        self.sf = evsf(self)    
        self.servers.append(reactor.listenTCP(10201, self.sf))
        
        self.engines = es.EngineService(InteractiveShell)
        ef = ev.VanillaEngineClientFactoryFromEngineService(self.engines)
        starterDeferred = defer.Deferred()
        def myNotifySetID():
            starterDeferred.callback(None)
        ef.notifySetID = myNotifySetID

        client = reactor.connectTCP('127.0.0.1', 10201, ef)
        self.clients.append(client)
        self.services.append(self.engines)
        self.engines.startService()
        return starterDeferred
        
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
    
    def registerEngine(self, remoteEngine, id):
        self.engine = remoteEngine
        self.engine.id = 0
        return 0
    
    def unregisterEngine(self, id):
        pass
    
    def registerSerializationTypes(self, *types):
        pass