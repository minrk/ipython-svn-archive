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
from twisted.python import components
from twisted.internet import reactor, defer


from ipython1.test import util
from ipython1.test  import completeenginetest as cet
from ipython1.kernel import engineservice as es, enginevanilla as ev

class EngineVanillaTest(cet.CompleteEngineTestCase):
#class EnginePBTest(util.DeferredTestCase):
        
    def setUp(self):
        #start one controller and connect one engine
        self.deferred = defer.Deferred()
        self.deferred.addCallback(self.printer)
#        self.deferred.callback(None)
        self.services = []
        self.clients = []
        self.servers = []
        self.sf = ev.VanillaEngineServerFactoryFromControllerService(self)
        self.servers.append(reactor.listenTCP(10201, self.sf))
        
        self.es = es.EngineService()
        ef = ev.IVanillaEngineClientFactory(self.es)
        client = reactor.connectTCP('127.0.0.1', 10201, ef)
        
        self.clients.append(client)
        self.services.append(self.es)
        self.es.startService()
        return self.deferred
        
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
        return dl
    
    def printer(self, result):
        print result
        return result
    
    def testA(self):
        pass
    
    def registerEngine(self, remoteEngine, id):
        self.e = remoteEngine
        self.deferred.callback(None)
        return 0
    
    def unregisterEngine(self, id):
        pass
    
    def registerSerializationTypes(self, *types):
        pass
