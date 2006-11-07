# encoding: utf-8
"""
test template for complete engine object
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
import zope.interface as zi

from ipython1.kernel import serialized, error, engineservice as es
from ipython1.test.util import DeferredTestCase

class CompleteEngineTestCase(DeferredTestCase):
    """A test for any completed engine object
    the engine object must be in self.engine"""
    class Empty:
        pass
    engine = es.completeEngine(Empty())
    
    def printer(self, r):
        print r
        return r
    
    def passer(self, r):
        return r
    
    def catchNotImplemented(self, f):
        try:
            f.raiseException()
        except NotImplementedError:
            pass
    
    def catchQueueCleared(self, f):
        try:
            f.raiseException()
        except error.QueueCleared:
            pass
    
    def testInterface(self):
        for base in es.IEngineComplete.getBases():
            self.assert_(base.providedBy(self.engine))
    
    def testInterfaceDeep(self):
        l = []
        for method in list(es.IEngineComplete):
            M = es.IEngineComplete[method]
            if isinstance(M, zi.interface.Method) and 'kill' not in method:
                f = getattr(self.engine, method, None)
                self.assert_(f is not None)
                d = f(*M.getSignatureInfo()['required'])
                # makes a minimum call, not a typical call
                d.addErrback(self.catchNotImplemented)
                d.addErrback(self.catchQueueCleared)
                l.append(d)
        D = defer.DeferredList(l)
        return D
    
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
            d.addErrback(self.catchNotImplemented)
        return d
    
    def testPushPull(self):
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        d = defer.succeed(None)
        l = []
        for o in objs:
            self.engine.push(key=o).addErrback(self.catchNotImplemented)
            value = self.engine.pull('key')
            d = self.assertDeferredEquals(value, o, d).addErrback(self.catchNotImplemented)
        d.addCallback(lambda _:self.engine.reset())
        d.addCallback(lambda _: self.engine.pull("a"))
        d.addCallback(lambda nd:
            self.assert_(isinstance(nd,error.NotDefined)))
        return d.addErrback(self.catchNotImplemented)
    
    def testPushPullArray(self):
        try:
            import numpy
        except:
            print 'no numpy, ',
            return
        a = numpy.random.random(10000)
        d = self.engine.push(a=a).addErrback(self.catchNotImplemented)
        d.addCallback(lambda _: self.engine.pull('a'))
        d.addCallback(lambda b: b==a)
        d.addCallback(lambda c: c.all())
        return self.assertDeferredEquals(d, True).addErrback(self.catchNotImplemented)
    
    def testPushPullSerialized(self):
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        d = defer.succeed(None)
        for o in objs:
            self.engine.pushSerialized(key=serialized.serialize(o, 'key')
                ).addErrback(self.catchNotImplemented)
            value = self.engine.pullSerialized('key')
            value.addCallback(lambda serial: serial.unpack())
            d = self.assertDeferredEquals(value,o,d).addErrback(self.catchNotImplemented)
        return d
    
    def testPullNamespace(self):
        ns = {'a':10,'b':"hi there",'c3':1.2342354,'door':{"p":(1,2)}}
        d = self.engine.push(**ns)
        d.addCallback(lambda _: self.engine.pullNamespace(*ns.keys()))
        d = self.assertDeferredEquals(d,ns)
        return d.addErrback(self.catchNotImplemented)
    
    def testGetResult(self):
        d = self.engine.getResult().addErrback(self.catchNotImplemented)
        d.addErrback(lambda f: self.assertRaises(IndexError, f.raiseException))
        d.addCallback(lambda _:self.engine.execute("a = 5"))
        d.addCallback(lambda _: self.engine.getResult())
        d = self.assertDeferredEquals(d, (self.engine.id, 0,"a = 5","",""))
        d.addCallback(lambda _: self.engine.getResult(0))
        d = self.assertDeferredEquals(d, (self.engine.id, 0,"a = 5","",""))
        return d.addErrback(self.catchNotImplemented)
    
    def testStatus(self):
        d = self.engine.status()
        d.addCallback(lambda s: isinstance(s, dict))
        return self.assertDeferredEquals(d, True).addErrback(self.catchNotImplemented)
    
