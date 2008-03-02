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


