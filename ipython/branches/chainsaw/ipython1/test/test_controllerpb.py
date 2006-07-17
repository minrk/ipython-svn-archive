"""This file contains unittests for the controlllerservice.py module.

Things that should be tested:
- Should the EngineService return Deferred objects?
- Run the same tests that are run in shell.py.
- Make sure that the Interface is really implemented.
- The startService and stopService methods.
"""

from twisted.trial import unittest
from twisted.internet import defer, protocol, reactor
from twisted.protocols import basic
from twisted.application import internet
from twisted.spread import pb

from ipython1.kernel import engineservice, controllerservice, enginepb, controllerpb
from ipython1.test.util import DeferredTestCase
from ipython1.kernel1p.kernelerror import NotDefined

class BasicControllerServiceTest(DeferredTestCase):
    
    def setUp(self):
        cf = pb.PBServerFactory(pb.Root())
        ef = pb.PBServerFactory(pb.Root())
        self.cs = controllerservice.ControllerService(10105,cf,10201,ef)
        cf.root = controllerpb.PerspectiveControllerFromService(self.cs)
        ef.root = cf.root
        self.cs.startService()
    
    def tearDown(self):
        self.cs.stopService()
    
    def testRegisterEngine(self):
        for id in range(10):
            f = pb.PBClientFactory()
            es = engineservice.EngineService('localhost', 10201, f)
            engine = enginepb.PerspectiveEngineFromService(es)
            testd = f.getRootObject().addCallbacks(engine._connect, engine._failure)
            
            d = self.assertDeferredEquals(testd, id)
        #return d
    
