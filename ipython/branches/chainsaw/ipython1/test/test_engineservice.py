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
from ipython1.kernel1p.kernelerror import NotDefined

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
            self.assertEquals(result, c)
            
    def testPutGet(self):
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        for o in objs:
            self.s.put("key",o)
            value = self.s.get("key")
            self.assertEquals(value,o)
        self.assertRaises(TypeError,self.s.put,10)
        self.assertRaises(TypeError,self.s.get,10)
        self.s.reset()
        self.assert_(isinstance(self.s.get("a"),NotDefined))
        
    def testUpdate(self):
        d = {"a": 10, "b": 34.3434, "c": "hi there"}
        self.s.update(d)
        for k in d.keys():
            value = self.s.get(k)
            self.assertEquals(value, d[k])
        self.assertRaises(TypeError, self.s.update, [1,2,2])
        
    def testCommand(self):
        self.assertRaises(IndexError,self.s.getCommand)
        self.s.execute("a = 5")
        self.assertEquals(self.s.getCommand(),(0,"a = 5","",""))
        self.assertEquals(self.s.getCommand(0),(0,"a = 5","",""))
        self.s.reset()
        self.assertEquals(self.s.getLastCommandIndex(),-1)
        self.assertRaises(IndexError,self.s.getCommand)
        
    def testPickle(self):
        goodPickle = 1.5647654
        import pickle
        package = pickle.dumps(goodPickle,2)
        self.assertEquals(self.s.putPickle("a",package),None)
        package = self.s.getPickle("a")
        finalValue = pickle.loads(package)
        self.assertEquals(finalValue, goodPickle)
