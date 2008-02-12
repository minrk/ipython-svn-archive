# encoding: utf-8
"""This file contains unittests for the kernel.task.py module.

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

import time

from twisted.internet import defer
from twisted.trial import unittest

from ipython1.kernel import task, controllerservice as cs, engineservice as es
from ipython1.kernel.multiengine import IMultiEngine
from ipython1.testutils.util import DeferredTestCase

def _printer(r):
    """passthrough callback for debugging"""
    print r
    return r

class TaskTest(DeferredTestCase):
    
    def setUp(self):
        self.c  = cs.ControllerService()
        self.c.startService()
        self.me = IMultiEngine(self.c)
        self.tc = task.TaskController(self.c)
        self.tc.failurePenalty = 0
        
        self.engines = []
        for i in range(1):
            e = es.EngineService()
            # e.startService()
            self.c.registerEngine(es.QueuedEngine(e), i)
            self.engines.append(e)
    
    def tearDown(self):
        self.c.stopService()
        for e in self.engines:
            # e.stopService()
            pass
    
    def testTaskIDs(self):
        l = []
        for i in range(16):
            d = self.tc.run(task.Task('a=5'))
            d = self.assertDeferredEquals(d, i)
            l.append(d)
        return defer.DeferredList(l)
    
    def testAbort(self):
        """Cannot do a proper abort test, because blocking execution prevents
        abort from being called before task completes"""
        t = task.Task('a=5')
        d = self.tc.abort(0)
        d = self.assertDeferredRaises(d, IndexError)
        d.addCallback(lambda _:self.tc.run(t))
        d.addCallback(self.tc.abort)
        d = self.assertDeferredRaises(d, IndexError)
        return d
    
    def testClears(self):
        d = self.me.execute('b=1', targets=0)
        t = task.Task('a=1', clearBefore=True, resultNames='b', clearAfter=True)
        d.addCallback(lambda _:self.tc.run(t))
        d.addCallback(self.tc.getTaskResult,block=True)
        d.addCallback(lambda tr: tr.failure)
        d = self.assertDeferredRaises(d, NameError) # check b for clearBefore
        d.addCallback(lambda _:self.me.pull('a', targets=0))
        d = self.assertDeferredRaises(d, NameError) # check a for clearAfter
        return d
    
    def testSimpleRetries(self):
        d = self.me.execute('i=0', targets=0)
        t = task.Task("i += 1\nassert i == 16", resultNames='i',retries=10)
        t2 = task.Task("i += 1\nassert i == 16", resultNames='i',retries=10)
        
        d.addCallback(lambda r: self.tc.run(t))
        d.addCallback(self.tc.getTaskResult, block=True)
        d.addCallback(lambda tr: tr.ns.i)
        d = self.assertDeferredRaises(d, AssertionError)
        
        d.addCallback(lambda r: self.tc.run(t2))
        d.addCallback(self.tc.getTaskResult, block=True)
        d.addCallback(lambda tr: tr.ns.i)
        d = self.assertDeferredEquals(d, 16)
        return d
    
    def testRecoveryTasks(self):
        t = task.Task("i=16", resultNames='i')
        t2 = task.Task("raise Exception", recoveryTask=t, retries = 2)
        
        d = self.tc.run(t2)
        d.addCallback(self.tc.getTaskResult, block=True)
        d.addCallback(lambda tr: tr.ns.i)
        d = self.assertDeferredEquals(d, 16)
        return d
    
    def testInfiniteRecoveryLoop(self):
        t = task.Task("raise Exception", retries = 5)
        t2 = task.Task("assert False", retries = 2, recoveryTask = t)
        t.recoveryTask = t2
        
        d = self.tc.run(t)
        d.addCallback(self.tc.getTaskResult, block=True)
        d.addCallback(lambda tr: tr.ns.i)
        d = self.assertDeferredRaises(d, AssertionError)
        return d
    
    def testSetupNS(self):
        d = self.me.execute('a=0', targets=0)
        ns = dict(a=1, b=0)
        t = task.Task("", setupNS=ns, resultNames=['a','b'])
        d.addCallback(lambda r: self.tc.run(t))
        d.addCallback(self.tc.getTaskResult, block=True)
        d.addCallback(lambda tr: {'a':tr.ns.a, 'b':tr['b']})
        d = self.assertDeferredEquals(d, ns)
        return d
        
    
    def testTaskResults(self):
        t1 = task.Task('a=5', resultNames='a')
        d = self.tc.run(t1)
        d.addCallback(self.tc.getTaskResult, block=True)
        d.addCallback(lambda tr: (tr.ns.a,tr['a'],tr.failure, tr.raiseException()))
        d = self.assertDeferredEquals(d, (5,5,None,None))
        
        t2 = task.Task('7=5')
        d.addCallback(lambda r: self.tc.run(t2))
        d.addCallback(self.tc.getTaskResult, block=True)
        d.addCallback(lambda tr: tr.ns)
        d = self.assertDeferredRaises(d, SyntaxError)
        
        t3 = task.Task('', resultNames='b')
        d.addCallback(lambda r: self.tc.run(t3))
        d.addCallback(self.tc.getTaskResult, block=True)
        d.addCallback(lambda tr: tr.ns)
        d = self.assertDeferredRaises(d, NameError)
        return d
    

class DependencyTest(unittest.TestCase):
    """The Tests for a Task's Dependency object"""
    
    def testDictDependency(self):
        d = dict(a=5, b=True)
        dep = task.Dependency(d)
        self.assertEquals(dep.test(d), True)
        d['c'] = 'asdf'
        self.assertEquals(dep.test(d), True)
        d['a'] = 4
        self.assertEquals(dep.test(d), False)
    
    def testListDependencies(self):
        d = task.Dependency()
        deplist = [('a', 5, '<'), ('b', 'asdf', 'in'), ['c', range(4), 'not in']]
        deplist.extend((['e', 15, '>='],['d', None]))
        # print deplist
        d.depend(deplist)
        dikt = dict(a=4, b='a', c=6, d=None, e=15)
        self.assertEquals(d.test(dikt), True)
        dikt['a'] = 5
        self.assertEquals(d.test(dikt), False)
        dikt['a'] = 4
        dikt['b'] = 'asdf'
        self.assertEquals(d.test(dikt), True)
        dikt['b'] = 7
        self.assertEquals(d.test(dikt), False)
        dikt['b'] = 'sd'
        dikt['c'] = 2
        self.assertEquals(d.test(dikt), False)
        dikt['c'] = 'asdf'
        dikt['d'] = 5
        self.assertEquals(d.test(dikt), False)
        del dikt['d']
        self.assertEquals(d.test(dikt), True)
        dikt['e'] = 'asdf'
        self.assertEquals(d.test(dikt), True)
        dikt['e'] = 14
        self.assertEquals(d.test(dikt), False)
        self.assertEquals(d.test({}), False)
        for key in 'abcde':
            d.undepend(key)
        self.assertEquals(d.test({}), True)
    
    def testStringDependency(self):
        s = """def test(properties):
        return properties.has_key('a')"""
        d = task.Dependency(s)
        dikt = {}
        self.assertEquals(d.test(dikt), False)
        dikt['a'] = 5
        self.assertEquals(d.test(dikt), True)
        s = """properties.get('a') >= 5 and len(properties) > 2"""
        d = task.Dependency(s)
        self.assertEquals(d.test(dikt), False)
        dikt['b'] = 1
        dikt['c'] = 2
        self.assertEquals(d.test(dikt), True)
        
        
            
    
    
    