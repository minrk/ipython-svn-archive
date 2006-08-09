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
from ipython1.test.util import DeferredTestCase
from ipython1.kernel.kernelerror import NotDefined

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
    
