#!/usr/bin/env python
# encoding: utf-8
"""Tests for pendingdeferred.py
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

from ipython1.testutils import tcommon
from ipython1.testutils.tcommon import *

from ipython1.testutils.util import DeferredTestCase

from twisted.internet import defer
import ipython1.kernel.pendingdeferred as pd
from ipython1.kernel import error


#-------------------------------------------------------------------------------
# Setup for inline and standalone doctests
#-------------------------------------------------------------------------------


# If you have standalone doctests in a separate file, set their names in the
# dt_files variable (as a single string  or a list thereof):
dt_files = []

# If you have any modules whose docstrings should be scanned for embedded tests
# as examples accorging to standard doctest practice, set them here (as a
# single string or a list thereof):
dt_modules = []

#-------------------------------------------------------------------------------
# Regular Unittests
#-------------------------------------------------------------------------------


class Foo(object):
    
    def bar(self, bahz):
        return defer.succeed('blahblah: %s' % bahz)

class TwoPhaseFoo(pd.PendingDeferredManager):
    
    def __init__(self, foo):
        self.foo = foo
        pd.PendingDeferredManager.__init__(self)

    @pd.twoPhase
    def bar(self, bahz):
        return self.foo.bar(bahz)
    
    def bam(self, bahz, block):
        def process_it(r, extra1, extra2='hi'):
            return r+' '+extra1+' '+extra2
        d = self.foo.bar(bahz)
        if block:
            d.addCallback(process_it, 'extra1', extra2='extra2')
            return d
        else:
            deferredID = self.getNextDeferredID()
            self.savePendingDeferred(deferredID, d, callback=process_it, arguments=(('extra1',), dict(extra2='extra2')))
            return defer.succeed(deferredID)

class PendingDeferredManagerTest(DeferredTestCase):
    
    def setUp(self):
        pass
        
    def tearDown(self):
        pass
        
    def testBasic(self):
        pdm = pd.PendingDeferredManager()
        dDict = {}
        for i in range(10):
            d = defer.Deferred()
            did = pdm.getNextDeferredID()
            pdm.savePendingDeferred(did, d)
            dDict[did] = d
        for did in dDict.keys()[0:5]:
            d = pdm.getPendingDeferred(did,block=True)
            dDict[did].callback('foo')
            d.addCallback(lambda r: self.assert_(r=='foo'))
        for did in dDict.keys()[5:10]:
            d = pdm.getPendingDeferred(did,block=False)
            d.addErrback(lambda f: self.assertRaises(error.ResultNotCompleted, f.raiseException))
        for did in dDict.keys()[5:10]:
            dDict[did].callback('foo')
            d = pdm.getPendingDeferred(did,block=False)
            d.addCallback(lambda r: self.assert_(r=='foo'))
        for did in dDict.keys():
            d = pdm.getPendingDeferred(did,False)
            d.addErrback(lambda f: self.assertRaises(error.InvalidDeferredID, f.raiseException))
    
    def testCallback(self):
        foo = Foo()
        pdm = TwoPhaseFoo(foo)
        d = pdm.bam('bam', block=True)
        d.addCallback(lambda r: self.assertEquals(r, "blahblah: bam extra1 extra2"))
        d.addCallback(lambda r: pdm.bam('bam', block=False))
        d.addCallback(lambda did: pdm.getPendingDeferred(did, True))
        d.addCallback(lambda r: self.assertEquals(r, "blahblah: bam extra1 extra2"))
        return d     
        
#-------------------------------------------------------------------------------
# Regular Unittests
#-------------------------------------------------------------------------------

# This ensures that the code will run either standalone as a script, or that it
# can be picked up by Twisted's `trial` test wrapper to run all the tests.
if tcommon.pexpect is not None:
    if __name__ == '__main__':
        unittest.main(testLoader=IPDocTestLoader(dt_files,dt_modules))
    else:
        testSuite = lambda : makeTestSuite(__name__,dt_files,dt_modules)
