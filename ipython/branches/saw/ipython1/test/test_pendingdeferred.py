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

import tcommon
from tcommon import *
from ipython1.test.util import DeferredTestCase


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


        
#-------------------------------------------------------------------------------
# Regular Unittests
#-------------------------------------------------------------------------------

# This ensures that the code will run either standalone as a script, or that it
# can be picked up by Twisted's `trial` test wrapper to run all the tests.

if __name__ == '__main__':
    unittest.main(testLoader=IPDocTestLoader(dt_files,dt_modules))
else:
    testSuite = lambda : makeTestSuite(__name__,dt_files,dt_modules)