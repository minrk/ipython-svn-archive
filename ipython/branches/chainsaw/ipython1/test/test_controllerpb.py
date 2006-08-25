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

from twisted.internet import reactor
from twisted.spread import pb

from ipython1.kernel import controllerservice as cs, serialized
from ipython1.kernel import controllerpb, util
from ipython1.test import multienginetest as met

class BasicControllerPBTest(met.MultiEngineTestCase):
    
    def setUp(self):
        self.rc = cs.ControllerService()
        self.rc.startService()
        self.sf = pb.PBServerFactory(controllerpb.IPBController(self.rc))
        self.s = reactor.listenTCP(10111, self.sf)
        self.cf = pb.PBClientFactory()
        self.c = reactor.connectTCP('127.0.0.1', 10111, self.cf)
        self.engines = []
        self.rc.registerSerializationTypes(serialized.Serialized)
        self.addEngine(1)
        return self.cf.getRootObject().addCallback(self.gotRoot)
    
    def gotRoot(self, root):
        self.controller = cs.IMultiEngine(root)
    
    def tearDown(self):
        self.rc.stopService()
        for e in self.engines:
            e.stopService()
        self.c.disconnect()
        return self.s.stopListening()
    
    def testInterfaces(self):
        p = list(self.controller.__provides__)
        l = [cs.IMultiEngine]
        self.assertEquals(p, l)
    
