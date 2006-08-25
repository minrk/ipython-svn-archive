from twisted.internet import defer
from ipython1.kernel import engineservice as es, serialized
from ipython1.kernel.error import NotDefined
from ipython1.test import util

class MultiEngineTestCase(util.DeferredTestCase):
    
    def setUp(self):
        """self.rc must implement controllerservice.IRemoteEngine.
        self.controller must implement IMultiEngine."""
        raise(NotImplementedError("Tests must override this method"))
    
    def tearDown(self):
        raise(NotImplementedError("Tests must override this method"))
    
    def addEngine(self, n=1):
        for i in range(n):
            e = es.completeEngine(es.EngineService())
            e.startService()
            self.rc.registerEngine(e, None)
            self.engines.append(e)
    
    def testDeferreds(self):
        l = [
        self.controller.execute(0, 'a=5'),
        self.controller.push(0, a=5),
        self.controller.push(0, a=5, b='asdf', c=[1,2,3]),
        self.controller.pull(0, 'a', 'b', 'c'),
        self.controller.pullNamespace(0, 'qwer', 'asdf', 'zcxv'),
        self.controller.getResult(0),
        self.controller.reset(0),
        self.controller.status(0)
        ]
        for d in l:
            self.assert_(isinstance(d, defer.Deferred))
        return defer.DeferredList(l)
    
    def testExecute(self):
        commands = [(0,"a = 5","",""),
            (1,"b = 10","",""),
            (2,"c = a + b","",""),
            (3,"print c","15\n",""),
            (4,"import math","",""),
            (5,"2.0*math.pi","6.2831853071795862\n","")]
        d = defer.succeed(None)
        for c in commands:
            result = self.controller.execute(0, c[1])
            d = self.assertDeferredEquals(result, [(0,)+c], d)
        return d
    
    def testPushPull(self):
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        d = defer.succeed(None)
        for o in objs:
            d0 = self.controller.push(0, key=o)
            value = self.controller.pull(0, 'key')
            d = self.assertDeferredEquals(value, [o] , d)
        self.controller.reset(0)
        d1 = self.controller.pull(0, "a").addCallback(lambda nd:
            self.assert_(isinstance(nd[0],NotDefined)))
        return defer.DeferredList([d, d0, d1])
    
    def testPushPullSerialized(self):
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        d = defer.succeed(None)
        for o in objs:
            self.controller.pushSerialized(0, key=serialized.serialize(o, 'key'))
            value = self.controller.pullSerialized(0, 'key')
            value.addCallback(lambda serial: serial[0].unpack())
            d = self.assertDeferredEquals(value,o,d)
        return d
    
    def testPullNamespace(self):
        ns = {'a':10,'b':"hi there",'c3':1.2342354,'door':{"p":(1,2)}}
        d = self.controller.push(0, **ns)
        d.addCallback(lambda _: self.controller.pullNamespace(0, *ns.keys()))
        d = self.assertDeferredEquals(d,[ns])
        return d
    
    def testResult(self):
        d = self.controller.getResult(0)
        d.addCallback(lambda r: r[0])
        d = self.assertDeferredRaises(d, IndexError)
        d.addCallback(lambda _:self.controller.execute(0, "a = 5"))
        d.addCallback(lambda _:self.controller.getResult(0))
        d = self.assertDeferredEquals(d,[(0, 0,"a = 5","","")])
        d.addCallback(lambda _:self.controller.getResult(0, 0))
        d = self.assertDeferredEquals(d,[(0, 0,"a = 5","","")])
        d.addCallback(lambda _:self.controller.reset(0))
        return d
    
    def testScatterGather(self):
        self.addEngine(15)
        try:
            import numpy
            a = numpy.random.random(100)
            d = self.controller.scatterAll('a', a)
            d.addCallback(lambda _: self.controller.gatherAll('a'))
            d.addCallback(lambda b: (a==b).all())
            d = self.assertDeferredEquals(d, True)
        except ImportError:
            print "no numpy"
            d = defer.succeed(None)
        l = range(100)
        d.addCallback(lambda _: self.controller.scatterAll('l', l))
        d.addCallback(lambda _: self.controller.gatherAll('l'))
        return self.assertDeferredEquals(d,l)
    

