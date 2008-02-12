# encoding: utf-8
"""
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

from twisted.internet import defer
from ipython1.testutils.util import DeferredTestCase
from ipython1.kernel.controllerservice import ControllerService
from ipython1.kernel import multiengine as me
from ipython1.kernel.tests.multienginetest import (IMultiEngineTestCase,
    ISynchronousMultiEngineTestCase,
    IFullTwoPhaseMultiEngineTestCase,
    IFullSynchronousTwoPhaseMultiEngineTestCase)
    
    
class BasicMultiEngineTestCase(DeferredTestCase, IMultiEngineTestCase):
    
    def setUp(self):
        self.controller = ControllerService()
        self.controller.startService()
        self.multiengine = me.IMultiEngine(self.controller)
        self.engines = []
        
    def tearDown(self):
        self.controller.stopService()
        for e in self.engines:
            e.stopService()


class SynchronousMultiEngineTestCase(DeferredTestCase, ISynchronousMultiEngineTestCase):
    
    def setUp(self):
        self.controller = ControllerService()
        self.controller.startService()
        self.multiengine = me.ISynchronousMultiEngine(me.IMultiEngine(self.controller))
        self.engines = []
        
    def tearDown(self):
        self.controller.stopService()
        for e in self.engines:
            e.stopService()


class FullTwoPhaseMultiEngineTestCase(DeferredTestCase, IFullTwoPhaseMultiEngineTestCase):
    
    def setUp(self):
        self.controller = ControllerService()
        self.controller.startService()
        self.multiengine = me.IFullTwoPhaseMultiEngine(me.ISynchronousMultiEngine(me.IMultiEngine(self.controller)))
        self.engines = []
        
    def tearDown(self):
        self.controller.stopService()
        for e in self.engines:
            e.stopService()


class FullSynchronousTwoPhaseMultiEngineTestCase(DeferredTestCase, IFullSynchronousTwoPhaseMultiEngineTestCase):
    
    def setUp(self):
        self.controller = ControllerService()
        self.controller.startService()
        multiengine = me.IMultiEngine(self.controller)
        multiengine = me.ISynchronousMultiEngine(multiengine)
        multiengine = me.IFullTwoPhaseMultiEngine(multiengine)
        self.multiengine = me.IFullSynchronousTwoPhaseMultiEngine(multiengine)
        self.engines = []
        
    def tearDown(self):
        self.controller.stopService()
        for e in self.engines:
            e.stopService()
