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
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

from twisted.internet import reactor, defer
from twisted.spread import pb, interfaces

from ipython1.kernel import controllerservice as cs, serialized
from ipython1.kernel import multienginepb, util

from ipython1.test.util import DeferredTestCase

class BasicControllerPBTest(DeferredTestCase):
    
    def setUp(self):
        self.rc = cs.ControllerService()
        self.rc.startService()
        self.root = multienginepb.IPBController(self.rc)
        self.root.remote_addNotifier = lambda _:None
        self.sf = pb.PBServerFactory(self.root)
        self.s = reactor.listenTCP(10111, self.sf)
        self.cf = pb.PBClientFactory()
        self.c = reactor.connectTCP('127.0.0.1', 10111, self.cf)
        self.engines = []
        self.addEngine(1)
        return self.cf.getRootObject().addCallback(self.gotRoot)
    
    def gotRoot(self, root):
        self.controller = cs.IEngineMultiplexer(root)
        return self.controller.deferred
    
    def tearDown(self):
        l=[]
        for e in self.engines+[self.rc]:
            e.stopService()
        self.c.disconnect()
        return self.s.stopListening()
    
    def testInterfaces(self):
        p = list(self.controller.__provides__)
        p.sort()
        l = [cs.IEngineMultiplexer, interfaces.IJellyable, INotifierParent]
        l.sort()
        return self.assertEquals(p, l)
    testInterfaces.skip = 'The ControllerPB tests need to be updated when ControllerPB is gone through.'
    
