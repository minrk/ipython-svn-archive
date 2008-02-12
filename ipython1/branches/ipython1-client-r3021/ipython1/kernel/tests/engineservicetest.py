# encoding: utf-8
"""
test template for complete engine object
"""
__docformat__ = "restructuredtext en"
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelley <benjaminrk@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import cPickle as pickle

from twisted.internet import defer, reactor
from twisted.python import failure
from twisted.application import service
import zope.interface as zi

from ipython1.kernel import newserialized
from ipython1.kernel import error
from ipython1.kernel.pickleutil import can, uncan
import ipython1.kernel.engineservice as es
from ipython1.core.interpreter import Interpreter
from ipython1.testutils.testgenerator import (EngineExecuteTestGenerator, 
    EnginePushPullTestGenerator, 
    EngineFailingExecuteTestGenerator,
    EngineGetResultTestGenerator)


#-------------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------------

    
# A sequence of valid commands run through execute
validCommands = ['a=5',
                 'b=10',
                 'c=a+b',
                 'import math',
                 '2.0*math.pi',
                 """def f():
    result = 0.0
    for i in range(10):
        result += i
""",
                 'if 1<2: a=5',
                 """import time
time.sleep(0.1)""",
                """from math import cos;
x = 1.0*cos(0.5)""", # Semicolons lead to Discard ast nodes that should be discarded
                """from sets import Set
s = Set()
   """, # Trailing whitespace should be allowed.
                """import math
math.cos(1.0)""", # Test a method call with a discarded return value
                """x=1.0234
a=5; b=10""", # Test an embedded semicolon
                """x=1.0234
a=5; b=10;""" # Test both an embedded and trailing semicolon
                 ]
                 
# A sequence of commands that raise various exceptions
invalidCommands = [('a=1/0',ZeroDivisionError),
                   ('print v',NameError),
                   ('l=[];l[0]',IndexError),
                   ("d={};d['a']",KeyError),
                   ("assert 1==0",AssertionError),
                   ("import abababsdbfsbaljasdlja",ImportError),
                   ("raise Exception()",Exception)]

def testf(x):
    return 2.0*x

globala = 99

def testg(x):
    return  globala*x

class IEngineCoreTestCase(object):
    """Test an IEngineCore implementer."""

    def createShell(self):
        return Interpreter()

    def catchQueueCleared(self, f):
        try:
            f.raiseException()
        except error.QueueCleared:
            pass
        
    def testIEngineCoreInterface(self):
        """Does self.engine claim to implement IEngineCore?"""
        self.assert_(es.IEngineCore.providedBy(self.engine))
        
    def testIEngineCoreInterfaceMethods(self):
        """Does self.engine have the methods and attributes in IEngineCore."""
        for m in list(es.IEngineCore):
            self.assert_(hasattr(self.engine, m))
            
    def testIEngineCoreDeferreds(self):
        d = self.engine.execute('a=5')
        d.addCallback(lambda _: self.engine.pull('a'))
        d.addCallback(lambda _: self.engine.getResult())
        d.addCallback(lambda _: self.engine.keys())
        d.addCallback(lambda _: self.engine.push(dict(a=10)))
        return d
    
    def testExecute(self):
        eTester = EngineExecuteTestGenerator(validCommands, self)
        d = eTester.performTests()
        return d

    def testExecuteFailures(self):
        cmds = [x[0] for x in invalidCommands]
        excpts = [x[1] for x in invalidCommands]
        eTester = EngineFailingExecuteTestGenerator(cmds, excpts, self)
        d = eTester.performTests()
        return d
            
    def testPushPull(self):
        objs = [10,"hi there",1.2342354,{"p":(1,2)},None]
        eTester = EnginePushPullTestGenerator(objs, self)
        d = eTester.performTests()
        d.addCallback(lambda _:self.engine.reset())
        d.addCallback(lambda _: self.engine.pull("a"))
        d.addErrback(lambda f: self.assertRaises(NameError, f.raiseException))
        return d        

    def testPushPullFailures(self):
        d = self.engine.pull('a')
        d.addErrback(lambda f: self.assertRaises(NameError, f.raiseException))
        d.addCallback(lambda _: self.engine.execute('l = lambda x: x'))
        d.addCallback(lambda _: self.engine.pull('l'))
        d.addErrback(lambda f: self.assertRaises(pickle.PicklingError, f.raiseException))
        d.addCallback(lambda _: self.engine.push(dict(l=lambda x: x)))
        d.addErrback(lambda f: self.assertRaises(pickle.PicklingError, f.raiseException))
        return d
        
    def testPushPullArray(self):
        try:
            import numpy
        except:
            print 'no numpy, ',
            return
        a = numpy.random.random(1000)
        d = self.engine.push(dict(a=a))
        d.addCallback(lambda _: self.engine.pull('a'))
        d.addCallback(lambda b: b==a)
        d.addCallback(lambda c: c.all())
        return self.assertDeferredEquals(d, True)
        
    def testPushFunction(self):
                    
        d = self.engine.pushFunction(dict(f=testf))
        d.addCallback(lambda _: self.engine.execute('result = f(10)'))
        d.addCallback(lambda _: self.engine.pull('result'))
        d.addCallback(lambda r: self.assertEquals(r, testf(10)))
        return d

    def testPullFunction(self):
        d = self.engine.pushFunction(dict(f=testf, g=testg))
        d.addCallback(lambda _: self.engine.pullFunction(('f','g')))
        d.addCallback(lambda r: self.assertEquals(r[0](10), testf(10)))
        return d
        
    def testPushFunctionGlobal(self):
        """Make sure that pushed functions pick up the user's namespace for globals."""
        d = self.engine.push(dict(globala=globala))
        d.addCallback(lambda _: self.engine.pushFunction(dict(g=testg)))
        d.addCallback(lambda _: self.engine.execute('result = g(10)'))
        d.addCallback(lambda _: self.engine.pull('result'))
        d.addCallback(lambda r: self.assertEquals(r, testg(10)))
        return d
        
    def testGetResultFailure(self):
        d = self.engine.getResult(None)
        d.addErrback(lambda f: self.assertRaises(IndexError, f.raiseException))
        d.addCallback(lambda _: self.engine.getResult(10))
        d.addErrback(lambda f: self.assertRaises(IndexError, f.raiseException))
        return d
            
    def testGetResult(self):
        eTester = EngineGetResultTestGenerator(validCommands, self)
        d = eTester.performTests()
        return d

    def testGetResultDefault(self):
        cmd = 'a=5'
        shell = self.createShell()
        shellResult = shell.execute(cmd)
        def popit(dikt, key):
            dikt.pop(key)
            return dikt
        d = self.engine.execute(cmd)
        d.addCallback(lambda _: self.engine.getResult())
        d.addCallback(lambda r: self.assertEquals(shellResult, popit(r,'id')))
        return d

    def testKeys(self):
        d = self.engine.keys()
        d.addCallback(lambda s: isinstance(s, list))
        d.addCallback(lambda r: self.assertEquals(r, True))
        return d
            
            
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
        d = self.engine.pushSerialized(dict(key=newserialized.serialize(12345)))
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
            self.engine.pushSerialized(dict(key=newserialized.serialize(o)))
            value = self.engine.pullSerialized('key')
            value.addCallback(lambda serial: newserialized.IUnSerialized(serial).getObject())
            d = self.assertDeferredEquals(value,o,d)
        return d

    def testPullSerializedFailures(self):
        d = self.engine.pullSerialized('a')
        d.addErrback(lambda f: self.assertRaises(NameError, f.raiseException))
        d.addCallback(lambda _: self.engine.execute('l = lambda x: x'))
        d.addCallback(lambda _: self.engine.pullSerialized('l'))
        d.addErrback(lambda f: self.assertRaises(pickle.PicklingError, f.raiseException))
        return d

class IEngineQueuedTestCase(object):
    """Test an IEngineQueued implementer."""
        
    def testIEngineQueuedInterface(self):
        """Does self.engine claim to implement IEngineQueued?"""
        self.assert_(es.IEngineQueued.providedBy(self.engine))
        
    def testIEngineQueuedInterfaceMethods(self):
        """Does self.engine have the methods and attributes in IEngireQueued."""
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
        result = self.engine.clearQueue()
        d1 = self.assertDeferredEquals(result, None)
        d1.addCallback(lambda _: self.engine.queueStatus())
        d2 = self.assertDeferredEquals(d1, {'queue':[], 'pending':'None'})
        return d2
        
    def testQueueStatus(self):
        result = self.engine.queueStatus()
        result.addCallback(lambda r: 'queue' in r and 'pending' in r)
        d = self.assertDeferredEquals(result, True)
        return d

class IEnginePropertiesTestCase(object):
    """Test an IEngineProperties implementor."""
    
    def testIEnginePropertiesInterface(self):
        """Does self.engine claim to implement IEngineProperties?"""
        self.assert_(es.IEngineProperties.providedBy(self.engine))
    
    def testIEnginePropertiesInterfaceMethods(self):
        """Does self.engine have the methods and attributes in IEngireProperties."""
        for m in list(es.IEngineProperties):
            self.assert_(hasattr(self.engine, m))
    
    def testGetSetProperties(self):
        dikt = dict(a=5, b='asdf', c=True, d=None, e=range(5))
        d = self.engine.setProperties(dikt)
        d.addCallback(lambda r: self.engine.getProperties())
        d = self.assertDeferredEquals(d, dikt)
        d.addCallback(lambda r: self.engine.getProperties(('c',)))
        d = self.assertDeferredEquals(d, {'c': dikt['c']})
        d.addCallback(lambda r: self.engine.setProperties(dict(c=False)))
        d.addCallback(lambda r: self.engine.getProperties(('c', 'd')))
        d = self.assertDeferredEquals(d, dict(c=False, d=None))
        return d
    
    def testClearProperties(self):
        dikt = dict(a=5, b='asdf', c=True, d=None, e=range(5))
        d = self.engine.setProperties(dikt)
        d.addCallback(lambda r: self.engine.clearProperties())
        d.addCallback(lambda r: self.engine.getProperties())
        d = self.assertDeferredEquals(d, {})
        return d
    
    def testDelHasProperties(self):
        dikt = dict(a=5, b='asdf', c=True, d=None, e=range(5))
        d = self.engine.setProperties(dikt)
        d.addCallback(lambda r: self.engine.delProperties(('b','e')))
        d.addCallback(lambda r: self.engine.hasProperties(('a','b','c','d','e')))
        d = self.assertDeferredEquals(d, [True, False, True, True, False])
        return d
    
    def testStrictDict(self):
        s = """from ipython1.kernel.engineservice import getEngine
p = getEngine(%s).properties"""%self.engine.id
        d = self.engine.execute(s)
        d.addCallback(lambda r: self.engine.execute("p['a'] = lambda _:None"))
        d = self.assertDeferredRaises(d, error.InvalidProperty)
        d.addCallback(lambda r: self.engine.execute("p['a'] = range(5)"))
        d.addCallback(lambda r: self.engine.execute("p['a'].append(5)"))
        d.addCallback(lambda r: self.engine.getProperties('a'))
        d = self.assertDeferredEquals(d, dict(a=range(5)))
        return d
        
    
