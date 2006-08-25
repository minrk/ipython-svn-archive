"""This file contains unittests for the kernel.engineservice.py module.

Things that should be tested:
- Should the EngineService return Deferred objects?
- Run the same tests that are run in shell.py.
- Make sure that the Interface is really implemented.
- The startService and stopService methods.
"""

#*****************************************************************************
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from twisted.internet import defer, reactor
from twisted.spread import pb

from ipython1.kernel import engineservice as es, controllerservice as cs, serialized
from ipython1.kernel import controllerpb, util
from ipython1.test.util import DeferredTestCase
from ipython1.kernel.error import NotDefined

class BasicControllerPBTest(DeferredTestCase):
    
    def setUp(self):
        self.cs = cs.ControllerService()
        self.cs.startService()
        self.sf = pb.PBServerFactory(controllerpb.IPBController(self.cs))
        self.s = reactor.listenTCP(10111, self.sf)
        self.cf = pb.PBClientFactory()
        self.c = reactor.connectTCP('127.0.0.1', 10111, self.cf)
        self.engines = []
        self.cs.registerSerializationTypes(serialized.Serialized)
        self.addEngine(1)
        return self.cf.getRootObject().addCallback(self.gotRoot)
    
    def gotRoot(self, root):
        self.controller = cs.IMultiEngine(root)
    
    def tearDown(self):
        self.cs.stopService()
        for e in self.engines:
            e.stopService()
        self.c.disconnect()
        return self.s.stopListening()
    
    def addEngine(self, n=1):
        for i in range(n):
            e = es.completeEngine(es.EngineService())
            e.startService()
            self.cs.registerEngine(e, None)
            self.engines.append(e)
    
    def printer(self, r):
        print r
        return r
    
    def testInterfaces(self):
        p = list(self.controller.__provides__)
        l = [cs.IMultiEngine]
        self.assertEquals(p, l)
    
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
        d = self.controller.execute(0, "a = 5")
        d = self.assertDeferredEquals(self.controller.getResult(0),[(0, 0,"a = 5","","")], d)
        d = self.assertDeferredEquals(self.controller.getResult(0, 0),[(0, 0,"a = 5","","")], d)
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
    
