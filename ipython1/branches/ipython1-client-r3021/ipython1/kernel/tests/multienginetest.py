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
from ipython1.kernel.util import printer
from ipython1.kernel.error import InvalidEngineID, NoEnginesRegistered
from ipython1.kernel.tests.engineservicetest import validCommands, invalidCommands
from ipython1.kernel.tests.tgenerator import (MultiEngineExecuteAllTestGenerator,
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

def isdid(did):
    if not isinstance(did, str):
        return False
    if not len(did)==40:
        return False
    return True


class IMultiEngineTestCase(IMultiEngineBaseTestCase):
    """A test for any object that implements IEngineMultiplexer.
    
    self.multiengine must be defined and implement IEngineMultiplexer.
    """
            
    def testIMultiEngineInterface(self):
        """Does self.engine claim to implement IEngineCore?"""
        self.assert_(me.IEngineMultiplexer.providedBy(self.multiengine))
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
        d.addCallback(lambda _: self.multiengine.getResult(targets=0))
        d.addCallback(lambda _: self.multiengine.reset(targets=0))
        d.addCallback(lambda _: self.multiengine.keys(targets=0))
        d.addCallback(lambda _: self.multiengine.pushSerialized(dict(a=newserialized.serialize(10)),targets=0))
        d.addCallback(lambda _: self.multiengine.pullSerialized('a',targets=0))
        d.addCallback(lambda _: self.multiengine.clearQueue(targets=0))
        d.addCallback(lambda _: self.multiengine.queueStatus(targets=0))
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
         # d.addCallback(lambda _: self.multiengine.getResult(targets=badID))   
         # d.addErrback(lambda f: self.assertRaises(InvalidEngineID, f.raiseException))
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
        d.addCallback(lambda _: self.multiengine.push(dict(a=5), targets=badID))
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
        d = self.multiengine.push(dict(key=objs[0]), targets=0)
        d.addCallback(lambda _: self.multiengine.pull('key', targets=0))
        d.addCallback(lambda r: self.assertEquals(r, [objs[0]]))
        d.addCallback(lambda _: self.multiengine.push(dict(key=objs[1]), targets=0))
        d.addCallback(lambda _: self.multiengine.pull('key', targets=0))
        d.addCallback(lambda r: self.assertEquals(r, [objs[1]]))
        d.addCallback(lambda _: self.multiengine.push(dict(key=objs[2]), targets=0))
        d.addCallback(lambda _: self.multiengine.pull('key', targets=0))
        d.addCallback(lambda r: self.assertEquals(r, [objs[2]]))        
        d.addCallback(lambda _: self.multiengine.push(dict(key=objs[3]), targets=0))
        d.addCallback(lambda _: self.multiengine.pull('key', targets=0))
        d.addCallback(lambda r: self.assertEquals(r, [objs[3]]))
        d.addCallback(lambda _: self.multiengine.reset(targets=0))
        d.addCallback(lambda _: self.multiengine.pull('a', targets=0))
        d.addErrback(lambda f: self.assertRaises(NameError, f.raiseException))
        return d
    
    def testPushPullAll(self):
        self.addEngine(4)
        d = self.multiengine.push(dict(a=10))
        d.addCallback(lambda _: self.multiengine.pull('a'))
        d.addCallback(lambda r: self.assert_(r==[10,10,10,10]))
        d.addCallback(lambda _: self.multiengine.push(dict(a=10, b=20)))
        d.addCallback(lambda _: self.multiengine.pull(('a','b')))
        d.addCallback(lambda r: self.assert_(r==4*[[10,20]]))
        d.addCallback(lambda _: self.multiengine.push(dict(a=10, b=20), targets=0))
        d.addCallback(lambda _: self.multiengine.pull(('a','b'), targets=0))  
        d.addCallback(lambda r: self.assert_(r==[[10,20]]))
        d.addCallback(lambda _: self.multiengine.push(dict(a=None, b=None), targets=0))
        d.addCallback(lambda _: self.multiengine.pull(('a','b'), targets=0))  
        d.addCallback(lambda r: self.assert_(r==[[None,None]]))
        return d
    
    def testPushPullSerialized(self):
        self.addEngine(1)
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]        
        d = self.multiengine.pushSerialized(dict(key=newserialized.serialize(objs[0])), targets=0)
        d.addCallback(lambda _: self.multiengine.pullSerialized('key', targets=0))
        d.addCallback(lambda serial: newserialized.IUnSerialized(serial[0]).getObject())
        d.addCallback(lambda r: self.assertEquals(r, objs[0]))
        d.addCallback(lambda _: self.multiengine.pushSerialized(dict(key=newserialized.serialize(objs[1])), targets=0))
        d.addCallback(lambda _: self.multiengine.pullSerialized('key', targets=0))
        d.addCallback(lambda serial: newserialized.IUnSerialized(serial[0]).getObject())
        d.addCallback(lambda r: self.assertEquals(r, objs[1]))
        d.addCallback(lambda _: self.multiengine.pushSerialized(dict(key=newserialized.serialize(objs[2])), targets=0))
        d.addCallback(lambda _: self.multiengine.pullSerialized('key', targets=0))
        d.addCallback(lambda serial: newserialized.IUnSerialized(serial[0]).getObject())
        d.addCallback(lambda r: self.assertEquals(r, objs[2]))        
        d.addCallback(lambda _: self.multiengine.pushSerialized(dict(key=newserialized.serialize(objs[3])), targets=0))
        d.addCallback(lambda _: self.multiengine.pullSerialized('key', targets=0))
        d.addCallback(lambda serial: newserialized.IUnSerialized(serial[0]).getObject())
        d.addCallback(lambda r: self.assertEquals(r, objs[3]))
        d.addCallback(lambda _: self.multiengine.reset(targets=0))
        d.addCallback(lambda _: self.multiengine.pullSerialized('a', targets=0))
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
        d = self.multiengine.execute(cmd, targets=target)
        d.addCallback(lambda _: self.multiengine.getResult(targets=target))
        d.addCallback(lambda r: self.assertEquals(shellResult, popit(r[0],'id')))
        return d
    
    def testGetResultFailure(self):
        self.addEngine(1)
        d = self.multiengine.getResult(None, targets=0)
        d.addErrback(lambda f: self.assertRaises(IndexError, f.raiseException))
        d.addCallback(lambda _: self.multiengine.getResult(10, targets=0))
        d.addErrback(lambda f: self.assertRaises(IndexError, f.raiseException))
        return d    
    
    def testPushFunction(self):
        self.addEngine(1)
        d = self.multiengine.pushFunction(dict(f=testf), targets=0)
        d.addCallback(lambda _: self.multiengine.execute('result = f(10)', targets=0))
        d.addCallback(lambda _: self.multiengine.pull('result', targets=0))
        d.addCallback(lambda r: self.assertEquals(r[0], testf(10)))
        d.addCallback(lambda _: self.multiengine.push(dict(globala=globala), targets=0))
        d.addCallback(lambda _: self.multiengine.pushFunction(dict(g=testg), targets=0))
        d.addCallback(lambda _: self.multiengine.execute('result = g(10)', targets=0))
        d.addCallback(lambda _: self.multiengine.pull('result', targets=0))
        d.addCallback(lambda r: self.assertEquals(r[0], testg(10)))
        return d
    
    def testPullFunction(self):
        self.addEngine(1)
        d = self.multiengine.push(dict(a=globala), targets=0)
        d.addCallback(lambda _: self.multiengine.pushFunction(dict(f=testf), targets=0))
        d.addCallback(lambda _: self.multiengine.pullFunction('f', targets=0))
        d.addCallback(lambda r: self.assertEquals(r[0](10), testf(10)))
        d.addCallback(lambda _: self.multiengine.execute("def g(x): return x*x", targets=0))
        d.addCallback(lambda _: self.multiengine.pullFunction(('f','g'),targets=0))
        d.addCallback(lambda r: self.assertEquals((r[0][0](10),r[0][1](10)), (testf(10), 100)))
        return d
    
    def testPushFunctionAll(self):
        self.addEngine(4)
        d = self.multiengine.pushFunction(dict(f=testf))
        d.addCallback(lambda _: self.multiengine.execute('result = f(10)'))
        d.addCallback(lambda _: self.multiengine.pull('result'))
        d.addCallback(lambda r: self.assertEquals(r, 4*[testf(10)]))
        d.addCallback(lambda _: self.multiengine.push(dict(globala=globala)))
        d.addCallback(lambda _: self.multiengine.pushFunction(dict(testg=testg)))
        d.addCallback(lambda _: self.multiengine.execute('result = testg(10)'))
        d.addCallback(lambda _: self.multiengine.pull('result'))
        d.addCallback(lambda r: self.assertEquals(r, 4*[testg(10)]))
        return d        
    
    def testPullFunctionAll(self):
        self.addEngine(4)
        d = self.multiengine.pushFunction(dict(f=testf))
        d.addCallback(lambda _: self.multiengine.pullFunction('f'))
        d.addCallback(lambda r: self.assertEquals([func(10) for func in r], 4*[testf(10)]))
        return d


class ISynchronousMultiEngineTestCase(IMultiEngineBaseTestCase):
    
    def testISynchronousMultiEngineInterface(self):
        """Does self.engine claim to implement IEngineCore?"""
        self.assert_(me.ISynchronousEngineMultiplexer.providedBy(self.multiengine))
        self.assert_(me.ISynchronousMultiEngine.providedBy(self.multiengine))
        
    def testExecute(self):
        self.addEngine(4)
        execute = self.multiengine.execute
        d = execute('a=5', targets=0, block=True)
        d.addCallback(lambda r: self.assert_(len(r)==1))
        d.addCallback(lambda _: execute('b=10'))
        d.addCallback(lambda r: self.assert_(len(r)==4))
        d.addCallback(lambda _: execute('c=30', block=False))
        d.addCallback(lambda did: self.assert_(isdid(did)))
        d.addCallback(lambda _: execute('d=[0,1,2]', block=False))
        d.addCallback(lambda did: self.multiengine.getPendingDeferred(did, True))
        d.addCallback(lambda r: self.assert_(len(r)==4))
        return d
    
    def testPushPull(self):
        data = dict(a=10, b=1.05, c=range(10), d={'e':(1,2),'f':'hi'})
        self.addEngine(4)
        push = self.multiengine.push
        pull = self.multiengine.pull
        d = push({'data':data}, targets=0)
        d.addCallback(lambda r: pull('data', targets=0))
        d.addCallback(lambda r: self.assertEqual(r,[data]))
        d.addCallback(lambda _: push({'data':data}))
        d.addCallback(lambda r: pull('data'))
        d.addCallback(lambda r: self.assertEqual(r,4*[data]))
        d.addCallback(lambda _: push({'data':data}, block=False))
        d.addCallback(lambda did: self.multiengine.getPendingDeferred(did, True))
        d.addCallback(lambda _: pull('data', block=False))
        d.addCallback(lambda did: self.multiengine.getPendingDeferred(did, True))
        d.addCallback(lambda r: self.assertEqual(r,4*[data]))       
        return d

    def testPushPullFunction(self):
        self.addEngine(4)
        pushf = self.multiengine.pushFunction
        pullf = self.multiengine.pullFunction
        push = self.multiengine.push
        pull = self.multiengine.pull
        execute = self.multiengine.execute
        d = pushf({'testf':testf}, targets=0)
        d.addCallback(lambda r: pullf('testf', targets=0))
        d.addCallback(lambda r: self.assertEqual(r[0](1.0), testf(1.0)))
        # d.addCallback(lambda _: execute('r = testf(10)', targets=0))
        # d.addCallback(lambda _: pull('r', targets=0))
        # d.addCallback(lambda r: self.assertEquals(r[0], testf(10)))
        # d.addCallback(lambda _: pushf({'testf':testf}, block=False))
        # d.addCallback(lambda did: self.multiengine.getPendingDeferred(did, True))
        # d.addCallback(lambda _: pullf('testf', block=False))
        # d.addCallback(lambda did: self.multiengine.getPendingDeferred(did, True))        
        # d.addCallback(lambda r: self.assertEqual(r[0](1.0), testf(1.0)))
        # d.addCallback(lambda _: execute("def g(x): return x*x", targets=0))
        # d.addCallback(lambda _: pullf(('testf','g'),targets=0))
        # d.addCallback(lambda r: self.assertEquals((r[0][0](10),r[0][1](10)), (testf(10), 100)))
        return d

    def testGetResult(self):
        shell = Interpreter()
        result1 = shell.execute('a=10')
        result1['id'] = 0
        result2 = shell.execute('b=20')
        result2['id'] = 0
        execute= self.multiengine.execute
        getResult = self.multiengine.getResult
        self.addEngine(1)
        d = execute('a=10')
        d.addCallback(lambda _: getResult())
        d.addCallback(lambda r: self.assertEquals(r[0], result1))
        d.addCallback(lambda _: execute('b=20'))
        d.addCallback(lambda _: getResult(1))
        d.addCallback(lambda r: self.assertEquals(r[0], result1))
        d.addCallback(lambda _: getResult(2, block=False))
        d.addCallback(lambda did: self.multiengine.getPendingDeferred(did, True))
        d.addCallback(lambda r: self.assertEquals(r[0], result2))
        return d

    def testReset(self):
        pass
    
    def testKeys(self):
        pass
    
    def testPushSerialized(self):
        pass
    
    def testPullSerialized(self):
        pass
    
    def testClearQueue(self):
        pass
    
    def testQueueStatus(self):
        pass
    
    def testSetProperties(self):
        pass
    
    def testGetProperties(self):
        pass
    
    def testHasProperties(self):
        pass

    def testDelProperties(self):
        pass
    
    def testclearProperties(self):
        pass
    
    def testGetIDs(self):
        pass


    
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





