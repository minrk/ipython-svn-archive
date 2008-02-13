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
from ipython1.kernel.tests.tasktest import ITaskControllerTestCase

#-------------------------------------------------------------------------------
# Tests
#-------------------------------------------------------------------------------

class BasicTaskControllerTestCase(DeferredTestCase, ITaskControllerTestCase):
    
    def setUp(self):
        self.controller  = cs.ControllerService()
        self.controller.startService()
        self.multiengine = IMultiEngine(self.controller)
        self.tc = task.ITaskController(self.controller)
        self.tc.failurePenalty = 0
        self.engines=[]
        
    def tearDown(self):
        self.controller.stopService()
        for e in self.engines:
            e.stopService()



class DependencyTest(unittest.TestCase):
    
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
