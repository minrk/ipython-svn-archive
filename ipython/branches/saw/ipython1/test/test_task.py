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

from ipython1.kernel import task, controllerservice as cs, engineservice as es
from ipython1.kernel.multiengine import IMultiEngine
from ipython1.test.util import DeferredTestCase

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
        d = self.me.execute(0,'b=1')
        t = task.Task('a=0', clearBefore=True, resultNames='b', clearAfter=True)
        d.addCallback(lambda _:self.tc.run(t))
        d.addCallback(self.tc.getTaskResult)
        d.addCallback(lambda tr: tr._failure)
        d = self.assertDeferredRaises(d, NameError) # check b for clearBefore
        d.addCallback(lambda _:self.me.pull(0,'a'))
        d = self.assertDeferredRaises(d, NameError) # check a for clearAfter
        return d
    
    def testResults(self):
        t = task.Task('a=5', resultNames='a')
        d = self.tc.run(t)
        d.addCallback(self.tc.getTaskResult)
        d.addCallback(lambda tr: (tr.a,tr['a'],tr._failure, tr.raiseException()))
        d = self.assertDeferredEquals(d, (5,5,None,None))
        return d
        
        

