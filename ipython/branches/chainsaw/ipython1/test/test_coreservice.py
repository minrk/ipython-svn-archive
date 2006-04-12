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
        self.ipcore = coreservice.CoreService()
        self.ipcore.startService()
        
    def tearDown(self):
        self.ipcore.stopService()
                
    def testExecute(self):
        commands = [(0,"a = 5","",""),
            (1,"b = 10","",""),
            (2,"c = a + b","",""),
            (3,"print c","15\n",""),
            (4,"import math","",""),
            (5,"2.0*math.pi","6.2831853071795862\n","")]
        
        d = self.assertDeferredEquals(self.ipcore.execute(commands[0][1]), 
                                      commands[0])
        for c in commands[1:]:
            d = self.assertDeferredEquals(self.ipcore.execute(c[1]), 
                                          c, chainDeferred=d)
        return d
        
    def testPutGet(self):
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        
        d = self.assertDeferredEquals(self.ipcore.put("key", objs[0]), None)
        d = self.assertDeferredEquals(self.ipcore.get("key"), objs[0], d)        
        for o in objs[1:]:
            d = self.assertDeferredEquals(self.ipcore.put("key",o), None, d)
            d = self.assertDeferredEquals(self.ipcore.get("key"), o, d)
        d = self.assertDeferredRaises(self.ipcore.put(10,10), TypeError, d)
        d = self.assertDeferredRaises(self.ipcore.get(10), TypeError, d)
        d = self.assertDeferredEquals(self.ipcore.reset(), None, d)
        d1 = self.ipcore.get("a")
        d1.addCallback(lambda r: isinstance(r, NotDefined))
        self.assertDeferredEquals(d1, True, d)
        return d1
        
    def testUpdate(self):
        data = {"a": 10, "b": 34.3434, "c": "hi there"}
        d = self.assertDeferredEquals(self.ipcore.update(data),None)
        for k in data.keys():
            self.assertDeferredEquals(self.ipcore.get(k), data[k], d)
        self.assertDeferredRaises(self.ipcore.update([1,2,2]), TypeError, d)
        return d

    def testCommands(self):
        d = self.assertDeferredRaises(self.ipcore.get_command(), IndexError)
        self.ipcore.execute("a = 5")
        self.assertDeferredEquals(self.ipcore.get_command(),(0,"a = 5","",""),d)
        self.assertDeferredEquals(self.ipcore.get_command(0),(0,"a = 5","",""),d)
        d = self.assertDeferredEquals(self.ipcore.reset(), None, d)
        self.assertDeferredEquals(self.ipcore.get_last_command_index(),-1,d)
        self.assertDeferredRaises(self.ipcore.get_command(),IndexError,d)
        return d
        
    def testPickle(self):
        good_pickle = 1.5647654
        import pickle
        package = pickle.dumps(good_pickle,2)
        d = self.assertDeferredEquals(self.ipcore.put_pickle("a",package),None)
        d1 = self.ipcore.get_pickle("a")
        d1.addCallback(lambda r: pickle.loads(r))
        d = self.assertDeferredEquals(d1,good_pickle,d)
        