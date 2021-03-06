# encoding: utf-8
"""This file contains unittests for the kernel.engineservice.py module.

Things that should be tested:

 - Should the EngineService return Deferred objects?
 - Run the same tests that are run in shell.py.
 - Make sure that the Interface is really implemented.
 - The startService and stopService methods.
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
from twisted.application.service import IService

from ipython1.kernel import engineservice as es
from ipython1.testutils.util import DeferredTestCase
from ipython1.kernel.tests.engineservicetest import \
    IEngineCoreTestCase, \
    IEngineSerializedTestCase, \
    IEngineQueuedTestCase, \
    IEnginePropertiesTestCase
    

class BasicEngineServiceTest(DeferredTestCase,
                             IEngineCoreTestCase, 
                             IEngineSerializedTestCase,
                             IEnginePropertiesTestCase):
    
    def setUp(self):
        self.engine = es.EngineService()
        self.engine.startService()
    
    def tearDown(self):
        return self.engine.stopService()

class QueuedEngineServiceTest(DeferredTestCase,
                              IEngineCoreTestCase, 
                              IEngineSerializedTestCase,
                              IEnginePropertiesTestCase,
                              IEngineQueuedTestCase):
                              
    def setUp(self):
        self.rawEngine = es.EngineService()
        self.rawEngine.startService()
        self.engine = es.IEngineQueued(self.rawEngine)
        
    def tearDown(self):
        return self.rawEngine.stopService()

 
