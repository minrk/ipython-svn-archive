"""This file contains unittests for the engineservice.py module.

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

from ipython1.kernel import engineservice
from ipython1.test.util import DeferredTestCase
from ipython1.kernel.kernelerror import NotDefined

class BasicEngineServiceTest(DeferredTestCase):

    def setUp(self):
        self.sf = protocol.ServerFactory()
        self.sf.protocol = basic.LineReceiver
        self.server = reactor.listenTCP(10201, self.sf)
        self.f = protocol.ClientFactory()
        self.f.protocol = basic.LineReceiver
        self.s = engineservice.EngineService()
        self.client = reactor.connectTCP('localhost',10202, self.f)
        self.s.startService()
        
    def tearDown(self):
        self.client.disconnect()
        del self.client
        return self.server.stopListening()
                
    def testExecute(self):
        commands = [(0,"a = 5","",""),
            (1,"b = 10","",""),
            (2,"c = a + b","",""),
            (3,"print c","15\n",""),
            (4,"import math","",""),
            (5,"2.0*math.pi","6.2831853071795862\n","")]
        for c in commands:
            result = self.s.execute(c[1])
            self.assertDeferredEquals(result, c)
    
    def testPushPull(self):
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        for o in objs:
            self.s.push(key=o)
            value = self.s.pull('key')
            self.assertDeferredEquals(value,o)
#        self.assertRaises(SyntaxError, self.s.push(1=2))

#        self.assertRaises(TypeError,self.s.pull,10)
        self.s.reset()
        d = self.s.pull("a").addCallback(lambda nd:
            self.assert_(isinstance(nd,NotDefined)))
        return d
    
    def testResult(self):
        #self.assertRaises(IndexError,self.s.getCommand)
        d = self.s.execute("a = 5")
        d = self.assertDeferredEquals(self.s.getResult(),(0,"a = 5","",""), d)
        d = self.assertDeferredEquals(self.s.getResult(0),(0,"a = 5","",""), d)
        d.addCallback(lambda _:self.s.reset())
        return d
#        return self.assertDeferredEquals(self.s.getLastCommandIndex(),-1, d)
        #self.assertRaises(IndexError,self.s.getCommand)
    
