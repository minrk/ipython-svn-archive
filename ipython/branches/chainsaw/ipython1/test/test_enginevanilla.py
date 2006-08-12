"""This file contains unittests for the enginepb.py module.

Things that should be tested:
The methods of Controller Service:
    registerEngine √
    unregisterEngine √
    execute/All √o
    push/Serial/All √/√/oo
    pull/Serial/All √/√/oo
    getResult/All √/o
    status/All oo
    reset/All oo
    *kill/All - do not test this, it calls reactor.stop

"""
from twisted.python import components, log
from twisted.internet import reactor, defer

defer.setDebugging(1)

import sys

from ipython1.test import util
from ipython1.test  import completeenginetest as cet
from ipython1.kernel import engineservice as es, enginevanilla as ev

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
        
        self.es = es.EngineService()
        ef = ev.VanillaEngineClientFactoryFromEngineService(self.es)
        starterDeferred = defer.Deferred()
        def myNotifySetID():
            starterDeferred.callback(None)
        ef.notifySetID = myNotifySetID

        client = reactor.connectTCP('127.0.0.1', 10201, ef)
        self.clients.append(client)
        self.services.append(self.es)
        self.es.startService()
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
        self.e = remoteEngine
        self.e.id = 0
        return 0
    
    def unregisterEngine(self, id):
        pass
    
    def registerSerializationTypes(self, *types):
        pass