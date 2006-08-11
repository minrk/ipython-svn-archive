"""This file contains unittests for the kernel.engineservice.py module.

Things that should be tested:
- Should the EngineService return Deferred objects?
- Run the same tests that are run in shell.py.
- Make sure that the Interface is really implemented.
- The startService and stopService methods.
"""

from twisted.internet import defer
from twisted.application.service import IService
from ipython1.kernel import engineservice as es
from ipython1.kernel import serialized
from ipython1.test.util import DeferredTestCase
from ipython1.kernel.error import NotDefined
import zope.interface as zi

class BasicEngineServiceTest(DeferredTestCase):
    
    def setUp(self):
        self.s = es.EngineService()
        self.s.startService()
    
    def tearDown(self):
        return self.s.stopService()
    
    def testInterfaces(self):
        p = list(self.s.__provides__)
        p.sort()
        l = [es.IEngineBase, es.IEngineSerialized, IService]
        l.sort()
        self.assertEquals(p, l)
        q = es.QueuedEngine(self.s)
        p = list(q.__provides__)
        p.sort()
        l.append(es.IEngineQueued)
        l.sort()
        self.assertEquals(p, l)
        c = es.completeEngine(q)
        p = list(c.__provides__)
        p.sort()
        l.append(es.IEngineComplete)
        l.sort()
        self.assertEquals(p, l)
        for base in es.IEngineComplete.getBases():
            self.assert_(base.providedBy(c))

    def testDeferreds(self):
        self.assert_(isinstance(self.s.execute('a=5'), defer.Deferred))
        self.assert_(isinstance(self.s.push(a=5), defer.Deferred))
        self.assert_(isinstance(self.s.push(a=5, b='asdf', c=[1,2,3]), defer.Deferred))
        self.assert_(isinstance(self.s.pull('a', 'b', 'c'), defer.Deferred))
        self.assert_(isinstance(self.s.pullNamespace('qwer', 'asdf', 'zcxv'), defer.Deferred))
        self.assert_(isinstance(self.s.getResult(), defer.Deferred))
        self.assert_(isinstance(self.s.reset(), defer.Deferred))
        self.assert_(isinstance(self.s.status(), defer.Deferred))
        self.assert_(not isinstance(self.s.id, defer.Deferred))
    
    def testCompletedEmptyEngine(self):
        class Empty:
            zi.implements(es.IEngineBase)
        ni = NotImplementedError
        c = es.completeEngine(Empty())
        self.assertDeferredRaises(c.execute('a=5'), ni)
        self.assertDeferredRaises(c.push(a=5), ni)
        self.assertDeferredRaises(c.pushSerialized(
                a=serialized.serialize([1,2,'a'], 'a')), ni)
        self.assertDeferredRaises(c.pull('a', 'b', 'c'), ni)
        self.assertDeferredRaises(c.pullSerialized('a', 'b', 'c'), ni)
        self.assertDeferredRaises(c.pullNamespace('qwer', 'asdf', 'zcxv'), ni)
        self.assertDeferredRaises(c.getResult(), ni)
        self.assertDeferredRaises(c.reset(), ni)
        self.assertDeferredRaises(c.status(), ni)
        self.assertDeferredRaises(c.clearQueue(), ni)
        self.assertEquals(c.id, None)
        
    def testExecute(self):
        commands = [(self.s.id, 0,"a = 5","",""),
            (self.s.id, 1,"b = 10","",""),
            (self.s.id, 2,"c = a + b","",""),
            (self.s.id, 3,"print c","15\n",""),
            (self.s.id, 4,"import math","",""),
            (self.s.id, 5,"2.0*math.pi","6.2831853071795862\n","")]
        for c in commands:
            result = self.s.execute(c[2])
            self.assertDeferredEquals(result, c)
    
    def testPushPull(self):
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        d = defer.succeed(None)
        for o in objs:
            self.s.push(key=o)
            value = self.s.pull('key')
            d = self.assertDeferredEquals(value,o, d)
        self.s.reset()
        d1 = self.s.pull("a").addCallback(lambda nd:
            self.assert_(isinstance(nd,NotDefined)))
        return (d, d1)
    
    def testPushPullSerialized(self):
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        d = defer.succeed(None)
        for o in objs:
            self.s.pushSerialized(key=serialized.serialize(o, 'key'))
            value = self.s.pullSerialized('key')
            value.addCallback(lambda serial: serial.unpack())
            d = self.assertDeferredEquals(value,o,d)
        return d
    
    def testPullNamespace(self):
        ns = {'a':10,'b':"hi there",'c3':1.2342354,'door':{"p":(1,2)}}
        d = self.s.push(**ns)
        d.addCallback(lambda _: self.s.pullNamespace(*ns.keys()))
        d = self.assertDeferredEquals(d,ns)
        return d
    
    def testResult(self):
        d = self.assertDeferredRaises(self.s.getResult(),IndexError)
        d.addCallback(lambda _:self.s.execute("a = 5"))
        d = self.assertDeferredEquals(self.s.getResult(),(self.s.id, 0,"a = 5","",""), d)
        d = self.assertDeferredEquals(self.s.getResult(0),(self.s.id, 0,"a = 5","",""), d)
        d.addCallback(lambda _:self.s.reset())
        return d
    
