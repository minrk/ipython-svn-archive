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
from ipython1.test.util import DeferredTestCase
from ipython1.kernel.controllerservice import ControllerService
from ipython1.kernel.multiengine import IMultiEngine
from ipython1.kernel import serialized
from ipython1.test.multienginetest import \
    IEngineMultiplexerTestCase, \
    IEngineCoordinatorTestCase
    
    
class BasicMultiEngineTestCase(DeferredTestCase,
    IEngineMultiplexerTestCase,
    IEngineCoordinatorTestCase):
    
    def setUp(self):
        self.controller = ControllerService()
        self.controller.startService()
        self.multiengine = IMultiEngine(self.controller)
        self.engines = []
        
    def tearDown(self):
        self.controller.stopService()
        for e in self.engines:
            e.stopService()