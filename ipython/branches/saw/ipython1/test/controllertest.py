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

from twisted.internet import defer
import zope.interface as zi

from ipython1.kernel import engineservice as es
from ipython1.kernel import serialized, error
from ipython1.test.util import DeferredTestCase
from ipython1.kernel.controllerservice import \
    IControllerCore


class IControllerCoreTestCase(object):
    """Tests for objects that implement IControllerCore.
    
    This test assumes that self.controller is defined and implements
    IControllerCore.
    """
    
    def testIControllerCoreInterface(self):
        """Does self.engine claim to implement IEngineCore?"""
        self.assert_(IControllerCore.providedBy(self.controller))
        
    def testIControllerCoreInterfaceMethods(self):
        """Does self.engine have the methods and attributes in IEngireCore."""
        for m in list(IControllerCore):
            self.assert_(hasattr(self.controller, m))
    
    def testRegisterUnregisterEngine(self):
        engine = es.EngineService()
        qengine = es.QueuedEngine(engine)
        regDict = self.controller.registerEngine(qengine, 0)
        # Do more complete testing of regDict registering multiple engines here
        self.assert_(isinstance(regDict, dict))
        self.controller.unregisterEngine(0)
        self.assert_(self.controller.engines.get(0, None) == None)
        
        
        