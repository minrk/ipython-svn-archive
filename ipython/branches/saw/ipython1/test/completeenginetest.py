# encoding: utf-8
"""
test template for complete engine object
"""
__docformat__ = "restructuredtext en"
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

from twisted.internet import defer
import zope.interface as zi

from ipython1.kernel import newserialized
from ipython1.kernel import error 
import ipython1.kernel.engineservice as es


class IEngineCoreTestCase(object):
    """Test an IEngineCore implementer."""

    def catchQueueCleared(self, f):
        try:
            f.raiseException()
        except error.QueueCleared:
            pass
        
    def testIEngineCoreInterface(self):
        """Does self.engine claim to implement IEngineCore?"""
        self.assert_(es.IEngineCore.providedBy(self.engine))
        
    def testIEngineCoreInterfaceMethods(self):
        """Does self.engine have the methods and attributes in IEngireCore."""
        for m in list(es.IEngineCore):
            self.assert_(hasattr(self.engine, m))
            
    def testIEngineCoreDeferreds(self):
        commands = [(self.engine.execute, ('a=5',)), 
            (self.engine.pull, ('a',)),
            (self.engine.pullNamespace, ('a',)),
            (self.engine.getResult, ()),
            (self.engine.keys, ())]
        dList = []
        for c in commands:
            d = c[0](*c[1])
            self.assert_(isinstance(d, defer.Deferred))
            dList.append(d)
        d = self.engine.push(a=5)
        self.assert_(isinstance(d, defer.Deferred))
        dList.append(d)
        D = defer.DeferredList(dList)
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
        return d
    
    def testPushPull(self):
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        d = defer.succeed(None)
        for o in objs:
            self.engine.push(key=o)
            value = self.engine.pull('key')
            d = self.assertDeferredEquals(value, o, d)
        d.addCallback(lambda _:self.engine.reset())
        d.addCallback(lambda _: self.engine.pull("a"))
        d.addCallback(lambda nd:
            self.assert_(isinstance(nd,error.NotDefined)))
        return d
    
    def testPushPullArray(self):
        try:
            import numpy
        except:
            print 'no numpy, ',
            return
        a = numpy.random.random(1000)
        d = self.engine.push(a=a)
        d.addCallback(lambda _: self.engine.pull('a'))
        d.addCallback(lambda b: b==a)
        d.addCallback(lambda c: c.all())
        return self.assertDeferredEquals(d, True)
    
    def testPullNamespace(self):
        ns = {'a':10,'b':"hi there",'c3':1.2342354,'door':{"p":(1,2)}}
        d = self.engine.push(**ns)
        d.addCallback(lambda _: self.engine.pullNamespace(*ns.keys()))
        d = self.assertDeferredEquals(d,ns)
        return d
    
    def testGetResult(self):
        d = self.engine.getResult()
        d.addErrback(lambda f: self.assertRaises(IndexError, f.raiseException))
        d.addCallback(lambda _:self.engine.execute("a = 5"))
        d.addCallback(lambda _: self.engine.getResult())
        d = self.assertDeferredEquals(d, (self.engine.id, 0,"a = 5","",""))
        d.addCallback(lambda _: self.engine.getResult(0))
        d = self.assertDeferredEquals(d, (self.engine.id, 0,"a = 5","",""))
        return d
    
    def testKeys(self):
        d = self.engine.keys()
        d.addCallback(lambda s: isinstance(s, list))
        return self.assertDeferredEquals(d, True)
            
            
class IEngineSerializedTestCase(object):
    """Test an IEngineCore implementer."""
        
    def testIEngineSerializedInterface(self):
        """Does self.engine claim to implement IEngineCore?"""
        self.assert_(es.IEngineSerialized.providedBy(self.engine))
        
    def testIEngineSerializedInterfaceMethods(self):
        """Does self.engine have the methods and attributes in IEngireCore."""
        for m in list(es.IEngineSerialized):
            self.assert_(hasattr(self.engine, m))
       
    def testIEngineSerializedDeferreds(self):
        dList = []
        d = self.engine.pushSerialized(key=newserialized.serialize(12345))
        self.assert_(isinstance(d, defer.Deferred))
        dList.append(d)
        d = self.engine.pullSerialized('key')
        self.assert_(isinstance(d, defer.Deferred))
        dList.append(d)
        D = defer.DeferredList(dList)
        return D
                
    def testPushPullSerialized(self):
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        d = defer.succeed(None)
        for o in objs:
            self.engine.pushSerialized(key=newserialized.serialize(o))
            value = self.engine.pullSerialized('key')
            value.addCallback(lambda serial: newserialized.IUnSerialized(serial).getObject())
            d = self.assertDeferredEquals(value,o,d)
        return d

class IEngineQueuedTestCase(object):
    """Test an IEngineCore implementer."""
        
    def testIEngineQueuedInterface(self):
        """Does self.engine claim to implement IEngineCore?"""
        self.assert_(es.IEngineQueued.providedBy(self.engine))
        
    def testIEngineQueuedInterfaceMethods(self):
        """Does self.engine have the methods and attributes in IEngireCore."""
        for m in list(es.IEngineQueued):
            self.assert_(hasattr(self.engine, m))
            
    def testIEngineQueuedDeferreds(self):
        dList = []
        d = self.engine.clearQueue()
        self.assert_(isinstance(d, defer.Deferred))
        dList.append(d)
        d = self.engine.queueStatus()
        self.assert_(isinstance(d, defer.Deferred))
        dList.append(d)
        D = defer.DeferredList(dList)
        return D
            
    def testClearQueue(self):
        return
        result = self.engine.clearQueue()
        d = self.assertDeferredEquals(result, True)
        return d
        
    def testQueueStatus(self):
        result = self.engine.queueStatus()
        result.addCallback(lambda r: 'queue' in r and 'pending' in r)
        d = self.assertDeferredEquals(result, True)
        return d
