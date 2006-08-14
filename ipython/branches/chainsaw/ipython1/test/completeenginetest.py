#!/usr/bin/env python
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
from ipython1.kernel import engineservice as es
from ipython1.kernel import serialized
from ipython1.test.util import DeferredTestCase
from ipython1.kernel.error import NotDefined

class CompleteEngineTestCase(DeferredTestCase):
    """A test for any completed engine object
    the engine object must be in self.e"""
    class Empty:
        pass
    e = es.completeEngine(Empty())
    
    def printer(self, r):
        print r
        return r
    
    def passer(self, r):
        return
    
    def testInterface(self):
        for base in es.IEngineComplete.getBases():
            self.assert_(base.providedBy(self.e))
    
    def testExecute(self):
        commands = [(self.e.id, 0,"a = 5","",""),
            (self.e.id, 1,"b = 10","",""),
            (self.e.id, 2,"c = a + b","",""),
            (self.e.id, 3,"print c","15\n",""),
            (self.e.id, 4,"import math","",""),
            (self.e.id, 5,"2.0*math.pi","6.2831853071795862\n","")]
        d = defer.succeed(None)
        for c in commands:
            result = self.e.execute(c[2])
            d = self.assertDeferredEquals(result, c, d)
        return d
    
    def testPushPull(self):
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        d = defer.succeed(None)
        for o in objs:
            self.e.push(key=o)
            value = self.e.pull('key')
            d = self.assertDeferredEquals(value,o, d)
        d.addCallback(lambda _:self.e.reset())
        d.addCallback(lambda _: self.e.pull("a"))
        d.addCallback(lambda nd:
            self.assert_(isinstance(nd,NotDefined)))
        return d
    
    def testPushPullArray(self):
        try:
            import numpy
        except:
            print 'no numpy'
            return
        a = numpy.random.random(10000)
        d = self.e.push(a=a)
        d.addCallback(lambda _: self.e.pull('a'))
        d.addCallback(lambda b: b==a)
        d.addCallback(lambda c: c.all())
        return self.assertDeferredEquals(d, True)
    
    def testPushPullSerialized(self):
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        d = defer.succeed(None)
        for o in objs:
            self.e.pushSerialized(key=serialized.serialize(o, 'key'))
            value = self.e.pullSerialized('key')
            value.addCallback(lambda serial: serial.unpack())
            d = self.assertDeferredEquals(value,o,d)
        return d
    
    def testPullNamespace(self):
        ns = {'a':10,'b':"hi there",'c3':1.2342354,'door':{"p":(1,2)}}
        d = self.e.push(**ns)
        d.addCallback(lambda _: self.e.pullNamespace(*ns.keys()))
        d = self.assertDeferredEquals(d,ns)
        return d
    
    def testGetResult(self):
        #d = self.assertDeferredRaises(self.e.getResult(),IndexError)
        d = self.e.execute("a = 5")
        d.addCallback(lambda _: self.e.getResult())
        d = self.assertDeferredEquals(d, (self.e.id, 0,"a = 5","",""))
        d.addCallback(lambda _: self.e.getResult(0))
        d = self.assertDeferredEquals(d, (self.e.id, 0,"a = 5","",""))
        return d
    
    def testStatus(self):
        pass
    
