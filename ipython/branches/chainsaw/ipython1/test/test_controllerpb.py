"""This file contains unittests for the controlllerservice.py module.

Things that should be tested:
- Should the EngineService return Deferred objects?
- Run the same tests that are run in shell.py.
- Make sure that the Interface is really implemented.
- The startService and stopService methods.
"""
from random import randint

from twisted.trial import unittest
from twisted.internet import defer, protocol, reactor
from twisted.protocols import basic
from twisted.application import internet
from twisted.spread import pb

from ipython1.kernel import engineservice, controllerservice, enginepb, controllerpb
from ipython1.kernel.remoteengine import Command
from ipython1.test.util import DeferredTestCase

class BasicControllerServiceTest(DeferredTestCase):
    
    def setUp(self):
        
        self.services = []
        self.factories = []
        self.cs = controllerservice.ControllerService()
        self.croot = controllerpb.ControlRoot(self.cs)
        self.eroot = controllerpb.RemoteEngineRoot(self.cs)
        self.cf = pb.PBServerFactory(self.croot)
        self.ef = pb.PBServerFactory(self.eroot)
        self.cs.setupControlFactory(10105, self.cf)
        self.cs.setupRemoteEngineFactory(10201, self.ef)
        
        self.f = pb.PBClientFactory()
        self.es = engineservice.EngineService('localhost', 10201, self.f)
        self.engine = enginepb.PerspectiveEngine(self.es)
        
        self.services.append(self.es)
        
        self.cs.startService()
        self.es.startService()
        return self.engine.d
    
    
    def tearDown(self):
        for s in self.services:
            try:
                s.stopService()
            except:
                pass
        return self.cs.stopService()
    
    def newEngine(self):
        f = pb.PBClientFactory()
        self.factories.append(f)
        es = engineservice.EngineService('localhost', 10201, f)
        self.services.append(es)
        engine = enginepb.PerspectiveEngine(es)
        
        return (engine.d,es)
    
    def printer(self, p):
        print p

    def testRegistration(self):
        (d, es) = self.newEngine()
        es.startService()
        return self.assertDeferredEquals(d,1)
    
    def testDisconnectReconnect(self):
        (d, es) = self.newEngine()
        es.startService()
        d.addCallback(self.cs.restartEngine)
        d.addCallback(lambda _: self.cs.engine[1].saveID)
        d = self.assertDeferredEquals(d, True)
        return d
    
    #copied from ipython1.test.test_corepb
    def testExecute(self):
#        return
        commands = [(0,"a = 5","",""),
            (1,"b = 10","",""),
            (2,"c = a + b","",""),
            (3,"print c","15\n",""),
            (4,"import math","",""),
            (5,"2.0*math.pi","6.2831853071795862\n","")]
            
        d = defer.succeed(None)
        for c in commands:
            d = self.assertDeferredEquals(self.cs.engine[0].submitCommand(Command("execute",c[1])), 
                                          c, chainDeferred=d)
        return d

