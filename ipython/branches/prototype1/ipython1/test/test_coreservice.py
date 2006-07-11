"""This file contains unittests for the coreservice.py module.

Things that should be tested:
- Should the CoreService return Deferred objects?
- Run the same tests that are run in shell.py.
- Make sure that the Interface is really implemented.
- The startService and stopService methods.
"""

from twisted.trial import unittest
from twisted.internet import defer

from ipython1.kernel import coreservice, corepb
from ipython1.test.util import DeferredTestCase
from ipython1.kernel1p.kernelerror import NotDefined

class BasicCoreServiceTest(DeferredTestCase):

    def setUp(self):
        self.s = coreservice.CoreService()
        self.s.startService()
        
    def tearDown(self):
        self.s.stopService()
                
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
        self.assertRaises(IndexError,self.s.get_command)
        self.s.execute("a = 5")
        self.assertEquals(self.s.get_command(),(0,"a = 5","",""))
        self.assertEquals(self.s.get_command(0),(0,"a = 5","",""))
        self.s.reset()
        self.assertEquals(self.s.get_last_command_index(),-1)
        self.assertRaises(IndexError,self.s.get_command)
        
    def testPickle(self):
        good_pickle = 1.5647654
        import pickle
        package = pickle.dumps(good_pickle,2)
        self.assertEquals(self.s.put_pickle("a",package),None)
        package = self.s.get_pickle("a")
        final_value = pickle.loads(package)
        self.assertEquals(final_value, good_pickle)
        