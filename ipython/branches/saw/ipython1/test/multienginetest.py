# encoding: utf-8
""""""
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

from ipython1.kernel import engineservice as es
from ipython1.kernel.multiengine import IEngineMultiplexer, IEngineCoordinator 
from ipython1.kernel import newserialized
from ipython1.kernel.error import NotDefined
from ipython1.test import util


class IMultiEngineBaseTestCase(object):
    """Basic utilities for working with multiengine tests.
    
    Some subclass should define:
    
    * self.multiengine
    * self.engines to keep track of engines for clean up"""

    def addEngine(self, n=1):
        for i in range(n):
            e = es.EngineService()
            e.startService()
            regDict = self.multiengine.registerEngine(es.QueuedEngine(e), None)
            e.id = regDict['id']
            self.engines.append(e)

class IEngineMultiplexerTestCase(IMultiEngineBaseTestCase):
    """A test for any object that implements IEngineMultiplexer.
    
    self.multiengine must be defined and implement IEngineMultiplexer.
    """
    
    def testIEngineMultiplexerInterface(self):
        """Does self.engine claim to implement IEngineCore?"""
        self.assert_(IEngineMultiplexer.providedBy(self.multiengine))
        
    def testIEngineMultiplexerInterfaceMethods(self):
        """Does self.engine have the methods and attributes in IEngireCore."""
        for m in list(IEngineMultiplexer):
            self.assert_(hasattr(self.multiengine, m))
    
    def testIEngineMultiplexerDeferreds(self):
        self.addEngine(1)
        l = [
        self.multiengine.execute(0, 'a=5'),
        self.multiengine.push(0, a=5),
        self.multiengine.push(0, a=5, b='asdf', c=[1,2,3]),
        self.multiengine.pull(0, 'a', 'b', 'c'),
        self.multiengine.pullNamespace(0, 'qwer', 'asdf', 'zcxv'),
        self.multiengine.getResult(0),
        self.multiengine.reset(0),
        self.multiengine.keys(0)
        ]
        for d in l:
            self.assert_(isinstance(d, defer.Deferred))
        return defer.DeferredList(l)
    
    def testExecute(self):
        self.addEngine(6)
        commands = [(0,"a = 5","",""),
            (1,"b = 10","",""),
            (2,"c = a + b","",""),
            (3,"print c","15\n",""),
            (4,"import math","",""),
            (5,"2.0*math.pi","6.2831853071795862\n","")]
        d = defer.succeed(None)
        for c in commands:
            result = self.multiengine.execute(0, c[1])
            d = self.assertDeferredEquals(result, [(0,)+c], d)
        return d
    
    def testPushPull(self):
        self.addEngine(1)
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        d = defer.succeed(None)
        for o in objs:
            d0 = self.multiengine.push(0, key=o)
            value = self.multiengine.pull(0, 'key')
            d = self.assertDeferredEquals(value, [o] , d)
        self.multiengine.reset(0)
        d1 = self.multiengine.pull(0, "a").addCallback(lambda nd:
            self.assert_(isinstance(nd[0],NotDefined)))
        return defer.DeferredList([d, d0, d1])
    
    def testPushPullSerialized(self):
        self.addEngine(1)
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        d = defer.succeed(None)
        for o in objs:
            self.multiengine.pushSerialized(0, key=newserialized.serialize(o))
            value = self.multiengine.pullSerialized(0, 'key')
            value.addCallback(lambda serial: newserialized.IUnSerialized(serial[0]).getObject())
            d = self.assertDeferredEquals(value,o,d)
        return d
    
    def testPullNamespace(self):
        self.addEngine(1)
        ns = {'a':10,'b':"hi there",'c3':1.2342354,'door':{"p":(1,2)}}
        d = self.multiengine.push(0, **ns)
        d.addCallback(lambda _: self.multiengine.pullNamespace(0, *ns.keys()))
        d = self.assertDeferredEquals(d,[ns])
        return d
    
    def testResult(self):
        self.addEngine(1)
        d = self.multiengine.getResult(0)
        d.addCallback(lambda r: r[0])
        d = self.assertDeferredRaises(d, IndexError)
        d.addCallback(lambda _:self.multiengine.execute(0, "a = 5"))
        d.addCallback(lambda _:self.multiengine.getResult(0))
        d = self.assertDeferredEquals(d,[(0, 0,"a = 5","","")])
        d.addCallback(lambda _:self.multiengine.getResult(0, 0))
        d = self.assertDeferredEquals(d,[(0, 0,"a = 5","","")])
        d.addCallback(lambda _:self.multiengine.reset(0))
        return d
    
    
class IEngineCoordinatorTestCase(IMultiEngineBaseTestCase):
    """A test for any object that implements IEngineCoordinator.
    
    self.multiengine must be defined and implement IEngineCoordinator.
    self.engine must be a list of engines.
    """
    
    def testIEngineCoordinatorInterface(self):
        """Does self.engine claim to implement IEngineCore?"""
        self.assert_(IEngineCoordinator.providedBy(self.multiengine))
        
    def testIEngineCoordinatorInterfaceMethods(self):
        """Does self.engine have the methods and attributes in IEngireCore."""
        for m in list(IEngineCoordinator):
            self.assert_(hasattr(self.multiengine, m))
    
    def testIEngineCoordinatorDeferreds(self):
        self.addEngine(1)
        l = [
        self.multiengine.scatterAll('a', range(10)),
        self.multiengine.gatherAll('a')
        ]
        for d in l:
            self.assert_(isinstance(d, defer.Deferred))
        return defer.DeferredList(l)
    
    def testScatterGather(self):
        self.addEngine(8)
        try:
            import numpy
            a = numpy.random.random(100)
            d = self.multiengine.scatterAll('a', a)
            d.addCallback(lambda _: self.multiengine.gatherAll('a'))
            d.addCallback(lambda b: (a==b).all())
            d = self.assertDeferredEquals(d, True)
        except ImportError:
            print "no numpy"
            d = defer.succeed(None)
        l = range(100)
        d.addCallback(lambda _: self.multiengine.scatterAll('l', l))
        d.addCallback(lambda _: self.multiengine.gatherAll('l'))
        return self.assertDeferredEquals(d,l)
    

