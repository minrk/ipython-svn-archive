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
        self.cs = controllerservice.ControllerService()
        self.root = controllerpb.PerspectiveControllerFromService(self.cs)
        self.cf = pb.PBServerFactory(self.root)
        self.ef = pb.PBServerFactory(self.root)
        self.cs.setupControlFactory(10105, self.cf)
        self.cs.setupRemoteEngineFactory(10201, self.ef)
        
        d = self.cs.startService()
        
        self.f = pb.PBClientFactory()
        self.es = engineservice.EngineService('localhost', 10201, self.f)
        self.engine = enginepb.PerspectiveEngineFromService(self.es)
        d = self.f.getRootObject().addCallback(self.gotRoot)
        
        self.es.startService()
        
        return d
    
    def tearDown(self):
        self.es.stopService()
        self.cs.stopService()
        
    def gotRoot(self, obj):
        self.root = obj
        return self.engine._connect(obj)
    
#    def testRegisterEngine(self):
#        f = pb.PBClientFactory()
#        es = engineservice.EngineService('localhost', 10201, f)
#        self.engine = enginepb.PerspectiveEngineFromService(es)
#        f.getRootObject().addCallback(self.gotRoot)
#        self.assertEquals(self.engine.id, 0)
    
    def testExecute(self):
        commands = [(0,"a = 5","",""),
            (1,"b = 10","",""),
            (2,"c = a + b","",""),
            (3,"print c","15\n",""),
            (4,"import math","",""),
            (5,"2.0*math.pi","6.2831853071795862\n","")]
            
        d = self.assertDeferredEquals(self.cs.engine[0].submitCommand(Command("execute",commands[0][1])), 
                                      commands[0])
        for c in commands[1:]:
            d = self.assertDeferredEquals(self.cs.engine[0].submitCommand(Command("execute",c[1])), 
                                          c, chainDeferred=d)
        return d

