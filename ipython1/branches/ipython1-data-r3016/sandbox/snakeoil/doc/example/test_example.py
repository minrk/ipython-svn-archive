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
dt_files = ['pydt.txt','pydt2.txt','pydt3.txt']

# List here the names of modules containing docstrings you want to scan for
# doctests.  You must list the *module* names, not the filenames, (so use
# ['foo'] and not ['foo.py']).
dt_modules = ['exmod']

# List here any regular, standalone Python scripts you want to treat as tests
# (each is run as a separate unittest).
test_scripts = ['uscriptex.py','uscriptex2.py']

#-------------------------------------------------------------------------------
# Regular Unittests
#-------------------------------------------------------------------------------
class FooTestCase(unittest.TestCase):
    """Tests for Foo"""
    def test_bar(self):
        """Test feature bar."""
        pass

# A unittest that uses the ParametricTestCase class.  See oilparam for a more
# detailed example

class ExampleTestCase(ParametricTestCase):

    #-------------------------------------------------------------------
    # A standard test method, just like for normal unittest usage.
    def test_foo(self):
        """Normal test for feature foo."""
        pass

    #-------------------------------------------------------------------
    # Testing methods that need parameters.  These can NOT be named test*,
    # since they would be picked up by unittest and called without
    # arguments.  Instead, call them anything else (I use tst*) and then
    # load them via the factories below.
    def tstX(self,i):
        "Test feature X with parameters."
        if i==3:
            # Test fails
            self.fail('i is bad, bad: %s' % i)

    def tstXX(self,i,j):
        "Test feature XX with parameters."
        pass

    #-------------------------------------------------------------------
    # Parametric test factories that create the test groups to call the
    # above tst* methods with their required arguments.
    def testip(self):
        """Independent parametric test factory.

        A separate setUp() call is made for each test returned by this method.

        You must return an iterable (list or generator is fine) containing
        tuples with the actual method to be called as the first argument,
        and the arguments for that call later."""
        return ((self.tstX,i) for i in range(5))

    def testsp(self):
        """Shared parametric test factory.

        A single setUp() call is made for all the tests returned by this
        method.
        """
        return ((self.tstXX,i,i+1) for i in range(5))


#-------------------------------------------------------------------------------
# This ensures that the code will run either standalone as a script, or that it
# can be picked up by the main oilrun test runner as part of a larger run.
if __name__ == '__main__':
    main(tests=make_test_suite(__name__,dt_files,dt_modules,test_scripts,False))
else:
    testSuite = lambda idt=True: \
                make_test_suite(__name__,dt_files,dt_modules,test_scripts,idt)
