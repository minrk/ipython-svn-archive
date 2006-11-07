# encoding: utf-8
"""This file contains unittests for the kernel.engineservice.py module.

Things that should be tested:

 - Should the EngineService return Deferred objects?
 - Run the same tests that are run in shell.py.
 - Make sure that the Interface is really implemented.
 - The startService and stopService methods.
"""

#*****************************************************************************
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from twisted.application.service import IService
from ipython1.kernel import controllerservice as cs, serialized
from ipython1.test import multienginetest as met

class BasicControllerServiceTest(met.MultiEngineTestCase):
    
    def setUp(self):
        self.controller  = self.rc = cs.ControllerService()
        self.controller.startService()
        self.engines = []
        self.controller.registerSerializationTypes(serialized.Serialized)
        self.addEngine(1)
    
    def tearDown(self):
        self.controller.stopService()
        for e in self.engines:
            e.stopService()
    
    def testInterfaces(self):
        p = list(self.controller.__provides__)
        p.sort()
        l = [cs.IController, IService]
        l.sort()
        #self.assertEquals(p, l)
        for base in cs.IController.getBases():
            self.assert_(base.providedBy(self.controller))
    
