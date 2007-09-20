#!/usr/bin/env python
# encoding: utf-8
"""Simple template for integrated tests.

This file should be renamed to

test_FOO.py

so that it is recognized by the overall test driver, which looks for all
test_*.py files in the current directory to extract tests from them.
"""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------
import unittest

# SnakeOil basic support
from snakeoil.oilrun import main, make_test_suite

# This is only needed if you want to write parametric tests
from snakeoil.oilparam import ParametricTestCase

#-------------------------------------------------------------------------------
# Setup for collecting tests from various sources
#-------------------------------------------------------------------------------

# List here the names of files (including their extension) that can be
# correctly read and run as doctests.
dt_files = []

# List here the names of modules containing docstrings you want to scan for
# doctests.  You must list the *module* names, not the filenames, (so use
# ['foo'] and not ['foo.py']).
dt_modules = []

# List here any regular, standalone Python scripts you want to treat as tests
# (each is run as a separate unittest).
test_scripts = []

#-------------------------------------------------------------------------------
# Regular Unittests
#-------------------------------------------------------------------------------
class FooTestCase(unittest.TestCase):
    """Tests for Foo"""
    def test_bar(self):
        """Test feature bar."""
        pass

#-------------------------------------------------------------------------------
# This ensures that the code will run either standalone as a script, or that it
# can be picked up by the main oilrun test runner as part of a larger run.
if __name__ == '__main__':
    main(tests=make_test_suite(__name__,dt_files,dt_modules,test_scripts,False))
else:
    testSuite = lambda idt=True: \
                make_test_suite(__name__,dt_files,dt_modules,test_scripts,idt)
