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

from twisted.internet import defer
from twisted.application.service import IService
from ipython1.kernel import engineservice as es, controllerservice as cs, serialized
from ipython1.test.util import DeferredTestCase
from ipython1.kernel.error import NotDefined

class BasicControllerServiceTest(DeferredTestCase):
    
    def setUp(self):
        self.cs = cs.ControllerService()
        self.cs.startService()
        self.engines = []
        self.cs.registerSerializationTypes(serialized.Serialized)
        self.addEngine(1)
    
    def tearDown(self):
        self.cs.stopService()
        for e in self.engines:
            e.stopService()
    
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
        p = list(self.cs.__provides__)
        p.sort()
        l = [cs.IController, IService]
        l.sort()
        self.assertEquals(p, l)
        for base in cs.IController.getBases():
            self.assert_(base.providedBy(self.cs))
    
    def testDeferreds(self):
        self.assert_(not isinstance(self.cs.engines[0].id, defer.Deferred))
        l = [
        self.cs.execute(0, 'a=5'),
        self.cs.push(0, a=5),
        self.cs.push(0, a=5, b='asdf', c=[1,2,3]),
        self.cs.pull(0, 'a', 'b', 'c'),
        self.cs.pullNamespace(0, 'qwer', 'asdf', 'zcxv'),
        self.cs.getResult(0),
        self.cs.reset(0),
        self.cs.status(0)
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
            result = self.cs.execute(0, c[1])
            d = self.assertDeferredEquals(result, [(0,)+c], d)
        return d
    
    def testPushPull(self):
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        d = defer.succeed(None)
        for o in objs:
            d0 = self.cs.push(0, key=o)
            value = self.cs.pull(0, 'key')
            d = self.assertDeferredEquals(value, [o] , d)
        self.cs.reset(0)
        d1 = self.cs.pull(0, "a").addCallback(lambda nd:
            self.assert_(isinstance(nd[0],NotDefined)))
        return defer.DeferredList([d, d0, d1])
    
    def testPushPullSerialized(self):
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        d = defer.succeed(None)
        for o in objs:
            self.cs.pushSerialized(0, key=serialized.serialize(o, 'key'))
            value = self.cs.pullSerialized(0, 'key')
            value.addCallback(lambda serial: serial[0].unpack())
            d = self.assertDeferredEquals(value,o,d)
        return d
    
    def testPullNamespace(self):
        ns = {'a':10,'b':"hi there",'c3':1.2342354,'door':{"p":(1,2)}}
        d = self.cs.push(0, **ns)
        d.addCallback(lambda _: self.cs.pullNamespace(0, *ns.keys()))
        d = self.assertDeferredEquals(d,[ns])
        return d
    
    def testResult(self):
        d = self.cs.getResult(0)
        d.addCallback(lambda r: r[0])
        d = self.assertDeferredRaises(d, IndexError)
        d.addCallback(lambda _:self.cs.execute(0, "a = 5"))
        d = self.assertDeferredEquals(self.cs.getResult(0),[(0, 0,"a = 5","","")], d)
        d = self.assertDeferredEquals(self.cs.getResult(0, 0),[(0, 0,"a = 5","","")], d)
        d.addCallback(lambda _:self.cs.reset(0))
        return d
    
    def testScatterGather(self):
        self.addEngine(15)
        try:
            import numpy
            a = numpy.random.random(100)
            d = self.cs.scatterAll('a', a)
            d.addCallback(lambda _: self.cs.gatherAll('a'))
            d.addCallback(lambda b: (a==b).all())
            d = self.assertDeferredEquals(d, True)
        except ImportError:
            print "no numpy"
            d = defer.succeed(None)
        l = range(100)
        d.addCallback(lambda _: self.cs.scatterAll('l', l))
        d.addCallback(lambda _: self.controller.gatherAll('l'))
        return self.assertDeferredEquals(d,l)
    
