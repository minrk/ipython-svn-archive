"""This file contains unittests for the controlllerservice.py module.

Things that should be tested:
- Should the EngineService return Deferred objects?
- Run the same tests that are run in shell.py.
- Make sure that the Interface is really implemented.
- The startService and stopService methods.
"""
import time

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
        self.root = controllerpb.PerspectiveControllerFromService(self.cs)
        self.cf = pb.PBServerFactory(self.root)
        self.ef = pb.PBServerFactory(self.root)
        self.cs.setupControlFactory(10105, self.cf)
        self.cs.setupRemoteEngineFactory(10201, self.ef)
        
        self.f = pb.PBClientFactory()
        self.es = engineservice.EngineService('localhost', 10201, self.f)
        self.engine = enginepb.PerspectiveEngineFromService(self.es)
        d = self.f.getRootObject().addCallback(self.gotRoot)
        
        self.services.append(self.es)
        
        self.cs.startService()
        self.es.startService()
        
        return d
    
    def gotRoot(self, obj):
        self.r = obj
        return self.engine._connect(obj)
    
    def tearDown(self):
        for s in self.services:
            s.stopService()
        return self.cs.stopService()
    
    
    def testRegisterEngines(self):
        d = defer.succeed(None)
        for id in range(2,8):
            f = pb.PBClientFactory()
            self.factories.append(f)
            es = engineservice.EngineService('localhost', 10201, f)
            self.services.append(es)
            engine = enginepb.PerspectiveEngineFromService(es)
            d2 = f.getRootObject().addCallbacks(engine._connect, engine._failure)
            d.addCallback(lambda _:d2)

            es.startService()
        d.addCallback(lambda _:self.cs.engine.keys())
        print self.cs.engine.keys()
        return self.assertDeferredEquals(d, range(id))
    
    #copied from ipython1.test.test_corepb
    def testExecute(self):
        commands = [(0,"a = 5","",""),
            (1,"b = 10","",""),
            (2,"c = a + b","",""),
            (3,"print c","15\n",""),
            (4,"import math","",""),
            (5,"2.0*math.pi","6.2831853071795862\n","")]
            
        d = defer.succeed(None)
        for e in self.cs.engine.values():
            for c in commands:
                d = self.assertDeferredEquals(e.submitCommand(Command("execute",c[1])), 
                                              c, chainDeferred=d)
        print self.cs.engine.keys()
        return d

