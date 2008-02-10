# encoding: utf-8
""""""
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

from twisted.internet import defer

from ipython1.kernel import engineservice as es
from ipython1.kernel import multiengine as me
from ipython1.kernel import newserialized
from ipython1.kernel.error import NotDefined
from ipython1.testutils import util
from ipython1.kernel import newserialized
from ipython1.kernel.error import InvalidEngineID, NoEnginesRegistered
from ipython1.kernel.tests.engineservicetest import validCommands, invalidCommands
from ipython1.testutils.testgenerator import (MultiEngineExecuteAllTestGenerator,
    MultiEngineFailingExecuteTestGenerator,
    MultiEngineGetResultTestGenerator)
from ipython1.core.interpreter import Interpreter

class IMultiEngineBaseTestCase(object):
    """Basic utilities for working with multiengine tests.
    
    Some subclass should define:
    
    * self.multiengine
    * self.engines to keep track of engines for clean up"""

    def createShell(self):
        return Interpreter()

    def addEngine(self, n=1):
        for i in range(n):
            e = es.EngineService()
            e.startService()
            regDict = self.controller.registerEngine(es.QueuedEngine(e), None)
            e.id = regDict['id']
            self.engines.append(e)


def testf(x):
    return 2.0*x

globala = 99

def testg(x):
    return  globala*x



class IMultiEngineTestCase(IMultiEngineBaseTestCase):
    """A test for any object that implements IEngineMultiplexer.
    
    self.multiengine must be defined and implement IEngineMultiplexer.
    """
            
    def testIMultiEngineInterface(self):
        """Does self.engine claim to implement IEngineCore?"""
        self.assert_(me.IEngineMultiplexer.providedBy(self.multiengine))
        self.assert_(me.IEngineMultiplexerAll.providedBy(self.multiengine))
        self.assert_(me.IMultiEngine.providedBy(self.multiengine))
           
    def testIEngineMultiplexerInterfaceMethods(self):
        """Does self.engine have the methods and attributes in IEngineCore."""
        for m in list(me.IEngineMultiplexer):
            self.assert_(hasattr(self.multiengine, m))
    
    def testIEngineMultiplexerDeferreds(self):
        self.addEngine(1)
        d = self.multiengine.execute('a=5', targets=0)
        d.addCallback(lambda _: self.multiengine.push(dict(a=5),targets=0))
        d.addCallback(lambda _: self.multiengine.push(dict(a=5, b='asdf', c=[1,2,3]),targets=0))
        d.addCallback(lambda _: self.multiengine.pull(('a','b','c'),targets=0))
        d.addCallback(lambda _: self.multiengine.getResult(0))
        d.addCallback(lambda _: self.multiengine.reset(0))
        d.addCallback(lambda _: self.multiengine.keys(0))
        d.addCallback(lambda _: self.multiengine.pushSerialized(dict(a=newserialized.serialize(10)),targets=0))
        d.addCallback(lambda _: self.multiengine.pullSerialized('a',targets=0))
        d.addCallback(lambda _: self.multiengine.clearQueue(0))
        d.addCallback(lambda _: self.multiengine.queueStatus(0))
        return d
    
    def testInvalidEngineID(self):
         self.addEngine(1)
         badID = 100
         d = self.multiengine.execute('a=5', targets=badID)
         d.addErrback(lambda f: self.assertRaises(InvalidEngineID, f.raiseException))
         d.addCallback(lambda _: self.multiengine.push(dict(a=5), targets=badID))
         d.addErrback(lambda f: self.assertRaises(InvalidEngineID, f.raiseException))
         d.addCallback(lambda _: self.multiengine.pull('a', targets=badID))     
         d.addErrback(lambda f: self.assertRaises(InvalidEngineID, f.raiseException))
         d.addCallback(lambda _: self.multiengine.getResult(targets=badID))   
         d.addErrback(lambda f: self.assertRaises(InvalidEngineID, f.raiseException))
         d.addCallback(lambda _: self.multiengine.reset(targets=badID))     
         d.addErrback(lambda f: self.assertRaises(InvalidEngineID, f.raiseException))   
         d.addCallback(lambda _: self.multiengine.keys(targets=badID))     
         d.addErrback(lambda f: self.assertRaises(InvalidEngineID, f.raiseException))
         d.addCallback(lambda _: self.multiengine.pushSerialized(dict(a=newserialized.serialize(10)), targets=badID))
         d.addErrback(lambda f: self.assertRaises(InvalidEngineID, f.raiseException))
         d.addCallback(lambda _: self.multiengine.pullSerialized('a', targets=badID))
         d.addErrback(lambda f: self.assertRaises(InvalidEngineID, f.raiseException))
         d.addCallback(lambda _: self.multiengine.queueStatus(targets=badID))
         d.addErrback(lambda f: self.assertRaises(InvalidEngineID, f.raiseException))
         return d
    
    def testNoEnginesRegistered(self):
        badID = 'all'
        d = self.multiengine.execute('a=5', targets=badID)
        d.addErrback(lambda f: self.assertRaises(NoEnginesRegistered, f.raiseException))
        d.addCallback(lambda _: self.multiengine.push(a=5, targets=badID))
        d.addErrback(lambda f: self.assertRaises(NoEnginesRegistered, f.raiseException))
        d.addCallback(lambda _: self.multiengine.pull('a', targets=badID))     
        d.addErrback(lambda f: self.assertRaises(NoEnginesRegistered, f.raiseException))
        d.addCallback(lambda _: self.multiengine.getResult(targets=badID))   
        d.addErrback(lambda f: self.assertRaises(NoEnginesRegistered, f.raiseException))
        d.addCallback(lambda _: self.multiengine.reset(targets=badID))     
        d.addErrback(lambda f: self.assertRaises(NoEnginesRegistered, f.raiseException))   
        d.addCallback(lambda _: self.multiengine.keys(targets=badID))     
        d.addErrback(lambda f: self.assertRaises(NoEnginesRegistered, f.raiseException))
        d.addCallback(lambda _: self.multiengine.pushSerialized(dict(a=newserialized.serialize(10)), targets=badID))
        d.addErrback(lambda f: self.assertRaises(NoEnginesRegistered, f.raiseException))
        d.addCallback(lambda _: self.multiengine.pullSerialized('a', targets=badID))
        d.addErrback(lambda f: self.assertRaises(NoEnginesRegistered, f.raiseException))
        d.addCallback(lambda _: self.multiengine.queueStatus(targets=badID))
        d.addErrback(lambda f: self.assertRaises(NoEnginesRegistered, f.raiseException))
        return d        
    
    def testExecute(self):
        self.addEngine(4)
        targets = [0,3]
        eTester = MultiEngineExecuteAllTestGenerator(validCommands, self, targets)
        d = eTester.performTests()
        return d
    
    def testExecuteFailures(self):
        self.addEngine(4)
        targets = [0,2]
        cmds = [x[0] for x in invalidCommands]
        excpts = [x[1] for x in invalidCommands]
        eTester = MultiEngineFailingExecuteTestGenerator(cmds, excpts, self, targets)
        d = eTester.performTests()
        return d
    
    def testExecuteAll(self):
        self.addEngine(2)
        eTester = MultiEngineExecuteAllTestGenerator(validCommands, self)
        d = eTester.performTests()
        return d
    
    def testExecuteAllFailures(self):
        self.addEngine(4)
        cmds = [x[0] for x in invalidCommands]
        excpts = [x[1] for x in invalidCommands]
        eTester = MultiEngineFailingExecuteTestGenerator(cmds, excpts, self)
        d = eTester.performTests()
        return d
    
    def testPushPull(self):
        self.addEngine(1)
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]        
        d = self.multiengine.push(0, key=objs[0])
        d.addCallback(lambda _: self.multiengine.pull(0, 'key'))
        d.addCallback(lambda r: self.assertEquals(r, [objs[0]]))
        d.addCallback(lambda _: self.multiengine.push(0, key=objs[1]))
        d.addCallback(lambda _: self.multiengine.pull(0, 'key'))
        d.addCallback(lambda r: self.assertEquals(r, [objs[1]]))
        d.addCallback(lambda _: self.multiengine.push(0, key=objs[2]))
        d.addCallback(lambda _: self.multiengine.pull(0, 'key'))
        d.addCallback(lambda r: self.assertEquals(r, [objs[2]]))        
        d.addCallback(lambda _: self.multiengine.push(0, key=objs[3]))
        d.addCallback(lambda _: self.multiengine.pull(0, 'key'))
        d.addCallback(lambda r: self.assertEquals(r, [objs[3]]))
        d.addCallback(lambda _: self.multiengine.reset(0))
        d.addCallback(lambda _: self.multiengine.pull(0, 'a'))
        d.addErrback(lambda f: self.assertRaises(NameError, f.raiseException))
        return d
    
    def testPushPullAll(self):
        self.addEngine(4)
        d = self.multiengine.pushAll(a=10)
        d.addCallback(lambda _: self.multiengine.pullAll('a'))
        d.addCallback(lambda r: self.assert_(r==[10,10,10,10]))
        d.addCallback(lambda _: self.multiengine.pushAll(a=10, b=20))
        d.addCallback(lambda _: self.multiengine.pullAll('a','b'))
        d.addCallback(lambda r: self.assert_(r==4*[[10,20]]))
        d.addCallback(lambda _: self.multiengine.push(0, a=10, b=20))
        d.addCallback(lambda _: self.multiengine.pull(0,'a','b'))  
        d.addCallback(lambda r: self.assert_(r==[[10,20]]))
        d.addCallback(lambda _: self.multiengine.push(0, a=None, b=None))
        d.addCallback(lambda _: self.multiengine.pull(0, 'a','b'))  
        d.addCallback(lambda r: self.assert_(r==[[None,None]]))
        return d
    
    def testPushPullSerialized(self):
        self.addEngine(1)
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]        
        d = self.multiengine.pushSerialized(0, key=newserialized.serialize(objs[0]))
        d.addCallback(lambda _: self.multiengine.pullSerialized(0, 'key'))
        d.addCallback(lambda serial: newserialized.IUnSerialized(serial[0]).getObject())
        d.addCallback(lambda r: self.assertEquals(r, objs[0]))
        d.addCallback(lambda _: self.multiengine.pushSerialized(0, key=newserialized.serialize(objs[1])))
        d.addCallback(lambda _: self.multiengine.pullSerialized(0, 'key'))
        d.addCallback(lambda serial: newserialized.IUnSerialized(serial[0]).getObject())
        d.addCallback(lambda r: self.assertEquals(r, objs[1]))
        d.addCallback(lambda _: self.multiengine.pushSerialized(0, key=newserialized.serialize(objs[2])))
        d.addCallback(lambda _: self.multiengine.pullSerialized(0, 'key'))
        d.addCallback(lambda serial: newserialized.IUnSerialized(serial[0]).getObject())
        d.addCallback(lambda r: self.assertEquals(r, objs[2]))        
        d.addCallback(lambda _: self.multiengine.pushSerialized(0, key=newserialized.serialize(objs[3])))
        d.addCallback(lambda _: self.multiengine.pullSerialized(0, 'key'))
        d.addCallback(lambda serial: newserialized.IUnSerialized(serial[0]).getObject())
        d.addCallback(lambda r: self.assertEquals(r, objs[3]))
        d.addCallback(lambda _: self.multiengine.reset(0))
        d.addCallback(lambda _: self.multiengine.pullSerialized(0, 'a'))
        d.addErrback(lambda f: self.assertRaises(NameError, f.raiseException))
        return d
        
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]    
        d = defer.succeed(None)
        for o in objs:
            self.multiengine.pushSerialized(0, key=newserialized.serialize(o))
            value = self.multiengine.pullSerialized(0, 'key')
            value.addCallback(lambda serial: newserialized.IUnSerialized(serial[0]).getObject())
            d = self.assertDeferredEquals(value,o,d)
        return d
            
    def testGetResult(self):
        self.addEngine(4)
        targets = [0,1,2]
        eTester = MultiEngineGetResultTestGenerator(validCommands, self, targets)
        d = eTester.performTests()
        return d
    
    def testGetResultDefault(self):
        self.addEngine(1)
        target = 0
        cmd = 'a=5'
        shell = self.createShell()
        shellResult = shell.execute(cmd)
        def popit(dikt, key):
            dikt.pop(key)
            return dikt
        d = self.multiengine.execute(target, cmd)
        d.addCallback(lambda _: self.multiengine.getResult(target))
        d.addCallback(lambda r: self.assertEquals(shellResult, popit(r[0],'id')))
        return d
    
    def testGetResultFailure(self):
        self.addEngine(1)
        d = self.multiengine.getResult(0, None)
        d.addErrback(lambda f: self.assertRaises(IndexError, f.raiseException))
        d.addCallback(lambda _: self.multiengine.getResult(0, 10))
        d.addErrback(lambda f: self.assertRaises(IndexError, f.raiseException))
        return d    
    
    def testPushFunction(self):
        self.addEngine(1)
        d = self.multiengine.pushFunction(0,f=testf)
        d.addCallback(lambda _: self.multiengine.execute(0,'result = f(10)'))
        d.addCallback(lambda _: self.multiengine.pull(0, 'result'))
        d.addCallback(lambda r: self.assertEquals(r[0], testf(10)))
        d.addCallback(lambda _: self.multiengine.push(0,globala=globala))
        d.addCallback(lambda _: self.multiengine.pushFunction(0,g=testg))
        d.addCallback(lambda _: self.multiengine.execute(0,'result = g(10)'))
        d.addCallback(lambda _: self.multiengine.pull(0, 'result'))
        d.addCallback(lambda r: self.assertEquals(r[0], testg(10)))
        return d
    
    def testPullFunction(self):
        self.addEngine(1)
        d = self.multiengine.push(0,a=globala)
        d.addCallback(lambda _: self.multiengine.pushFunction(0,f=testf))
        d.addCallback(lambda _: self.multiengine.pullFunction(0, 'f'))
        d.addCallback(lambda r: self.assertEquals(r[0](10), testf(10)))
        return d
    
    def testPushFunctionAll(self):
        self.addEngine(4)
        d = self.multiengine.pushFunctionAll(f=testf)
        d.addCallback(lambda _: self.multiengine.executeAll('result = f(10)'))
        d.addCallback(lambda _: self.multiengine.pullAll('result'))
        d.addCallback(lambda r: self.assertEquals(r, 4*[testf(10)]))
        d.addCallback(lambda _: self.multiengine.pushAll(globala=globala))
        d.addCallback(lambda _: self.multiengine.pushFunctionAll(testg=testg))
        d.addCallback(lambda _: self.multiengine.executeAll('result = testg(10)'))
        d.addCallback(lambda _: self.multiengine.pullAll('result'))
        d.addCallback(lambda r: self.assertEquals(r, 4*[testg(10)]))
        return d        
    
    def testPullFunctionAll(self):
        self.addEngine(4)
        d = self.multiengine.pushFunctionAll(f=testf)
        d.addCallback(lambda _: self.multiengine.pullFunctionAll('f'))
        d.addCallback(lambda r: self.assertEquals([func(10) for func in r], 4*[testf(10)]))
        return d


class ISynchronousMultiEngineTestCase(IMultiEngineBaseTestCase):
    
    def testIMultiEngineInterface(self):
        """Does self.engine claim to implement IEngineCore?"""
        self.assert_(me.ISynchronousEngineMultiplexer.providedBy(self.multiengine))
        self.assert_(me.ISynchronousEngineMultiplexerAll.providedBy(self.multiengine))
        self.assert_(me.ISynchronousMultiEngine.providedBy(self.multiengine))
        
    def testExecute(self):
        self.addEngine(4)
        d = self.multiengine.execute(True, 0, 'a=5')
        d.addCallback(lambda _: self.assert_(True))
        return d

class ITwoPhaseMultiEngineTestCase(IMultiEngineBaseTestCase):
    pass



class IMultiEngineCoordinator(IMultiEngineBaseTestCase):
    pass

class ITwoPhaseMultiEngineCoordinator(IMultiEngineBaseTestCase):
    pass


class IMultiEngineExtras(IMultiEngineBaseTestCase):
    pass

class ITwoPhaseMultiEngineExtras(IMultiEngineBaseTestCase):
    pass


class IFullTwoPhaseMultiEngine(IMultiEngineBaseTestCase):
    pass


class IFullSynchronousTwoPhaseMultiEngine(IMultiEngineBaseTestCase):
    pass





