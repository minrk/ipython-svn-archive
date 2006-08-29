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

from ipython1.core.shell import InteractiveShell
from ipython1.kernel import serialized, error, engineservice as es
from ipython1.test import util
# from ipython1.test.completeenginetest import CompleteEngineTestCase

class BasicEngineServiceTest(util.DeferredTestCase):
    
    def setUp(self):
        self.engine = es.EngineService(InteractiveShell)
        self.engine.startService()
    
    def tearDown(self):
        return self.engine.stopService()
    
    def testInterfaces(self):
        p = list(self.engine.__provides__)
        p.sort()
        l = [es.IEngineBase, es.IEngineSerialized, IService]
        l.sort()
        self.assertEquals(p, l)
        q = es.QueuedEngine(self.engine)
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
        self.assert_(isinstance(self.engine.execute('a=5'), defer.Deferred))
        self.assert_(isinstance(self.engine.push(a=5), defer.Deferred))
        self.assert_(isinstance(self.engine.push(a=5, b='asdf', c=[1,2,3]), defer.Deferred))
        self.assert_(isinstance(self.engine.pull('a', 'b', 'c'), defer.Deferred))
        self.assert_(isinstance(self.engine.pullNamespace('qwer', 'asdf', 'zcxv'), defer.Deferred))
        self.assert_(isinstance(self.engine.getResult(), defer.Deferred))
        self.assert_(isinstance(self.engine.reset(), defer.Deferred))
        self.assert_(isinstance(self.engine.status(), defer.Deferred))
        self.assert_(not isinstance(self.engine.id, defer.Deferred))
    
    def testCompletedEmptyEngine(self):
        class Empty:
            pass
        ni = NotImplementedError
        c = es.completeEngine(Empty())
        d = self.assertDeferredRaises(c.execute('a=5'), ni)
        d = self.assertDeferredRaises(c.push(a=5), ni, d)
        d = self.assertDeferredRaises(c.pushSerialized(
                a=serialized.serialize([1,2,'a'], 'a')), ni, d)
        d = self.assertDeferredRaises(c.pull('a', 'b', 'c'), ni, d)
        d = self.assertDeferredRaises(c.pullSerialized('a', 'b', 'c'), ni, d)
        d = self.assertDeferredRaises(c.pullNamespace('qwer', 'asdf', 'zcxv'), ni, d)
        d = self.assertDeferredRaises(c.getResult(), ni, d)
        d = self.assertDeferredRaises(c.reset(), ni, d)
        d = self.assertDeferredRaises(c.status(), ni, d)
        d = self.assertDeferredRaises(c.clearQueue(), ni, d)
        return self.assertEquals(c.id, None, d)
        
    def testExecute(self):
        commands = [(self.engine.id, 0,"a = 5","",""),
            (self.engine.id, 1,"b = 10","",""),
            (self.engine.id, 2,"c = a + b","",""),
            (self.engine.id, 3,"print c","15\n",""),
            (self.engine.id, 4,"import math","",""),
            (self.engine.id, 5,"2.0*math.pi","6.2831853071795862\n","")]
        d = defer.succeed(None)
        for c in commands:
            result = self.engine.execute(c[2])
            d = self.assertDeferredEquals(result, c, d)
        return d
    
    def testPushPull(self):
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        d = defer.succeed(None)
        for o in objs:
            self.engine.push(key=o)
            value = self.engine.pull('key')
            d = self.assertDeferredEquals(value,o, d)
        d.addCallback(lambda _:self.engine.reset())
        d.addCallback(lambda _: self.engine.pull("a"))
        d.addCallback(lambda nd:
            self.assert_(isinstance(nd,error.NotDefined)))
        return d
    
    def testPushPullSerialized(self):
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        d = defer.succeed(None)
        for o in objs:
            self.engine.pushSerialized(key=serialized.serialize(o, 'key'))
            value = self.engine.pullSerialized('key')
            value.addCallback(lambda serial: serial.unpack())
            d = self.assertDeferredEquals(value,o,d)
        return d
    
    def testPullNamespace(self):
        ns = {'a':10,'b':"hi there",'c3':1.2342354,'door':{"p":(1,2)}}
        d = self.engine.push(**ns)
        d.addCallback(lambda _: self.engine.pullNamespace(*ns.keys()))
        d = self.assertDeferredEquals(d,ns)
        return d
    
    def testGetResult(self):
        d = self.assertDeferredRaises(self.engine.getResult(),IndexError)
        d.addCallback(lambda _:self.engine.execute("a = 5"))
        d = self.assertDeferredEquals(self.engine.getResult(),(self.engine.id, 0,"a = 5","",""), d)
        d = self.assertDeferredEquals(self.engine.getResult(0),(self.engine.id, 0,"a = 5","",""), d)
        d.addCallback(lambda _:self.engine.reset())
        return d
    
    def testStatus(self):
        pass
        # When mpi support is enabled, the following is not true.
        #return self.assertDeferredEquals(self.engine.status(), {})