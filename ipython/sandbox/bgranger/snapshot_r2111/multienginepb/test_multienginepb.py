#!/usr/bin/env python
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
# Doctests
#-------------------------------------------------------------------------------

# Module imports
import tcommon
from tcommon import *

# If you have standalone doctests in a separate file, set their names in the
# dt_files variable (as a single string  or a list thereof):
dt_files = ['tst_multienginepb.txt']

# If you have any modules whose docstrings should be scanned for embedded tests
# as examples accorging to standard doctest practice, set them here (as a
# single string or a list thereof):
dt_modules = None


#-------------------------------------------------------------------------------
# Unittests
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
        self.root = multienginepb.IPBMultiEngine(self.rc)
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
    testInterfaces.skip = 'The MultiEnginePB tests need to be updated when multienginepb.py is updated.'
    
    def testMessageSizeLimit(self):
        pass
    testMessageSizeLimit.skip = 'testMessageSizeLimit needs to be implemented in test_multienginepb.py.'
    
    def testInvalidTargets(self):
        pass
    testInvalidTargets.skip = 'add a test to make sure that InvalidEngineID is being raised appropriately.'
    
#-------------------------------------------------------------------------------
# Test coordination
#-------------------------------------------------------------------------------
 
# This ensures that the code will run either standalone as a script, or that it
# can be picked up by Twisted's `trial` test wrapper to run all the tests.

if __name__ == '__main__':
    unittest.main(testLoader=IPDocTestLoader(dt_files,dt_modules))
else:
    testSuite = lambda : makeTestSuite(__name__,dt_files,dt_modules)
