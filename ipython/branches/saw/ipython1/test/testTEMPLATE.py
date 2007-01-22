#!/usr/bin/env python
"""Simple template for unit tests.

This file should be renamed to

test_FEATURE.py

so that it is recognized by the overall test driver (Twisted's 'trial'), which
looks for all test_*.py files in the current directory to extract tests from
them.
"""

# Module imports
import tcommon

# WARNING: do NOT put a reload(tcommon) here!!!  It screws up running of the
# combined test suites by leaving multiple copies of the tcommon module in
# memory.  The resulting errors are extremely strange.

from tcommon import *

# If you have standalone doctests in a separate file, load them here and
# assign them to the __doc__ attribute, so doctest can pick them up:
#__doc__ = open(test_path('test_FEATURE.txt'), 'r').read()

# If you have any module whose docstrings should be scanned for embedded tests
# as examples (accorging to standard doctest practice), set it here:
DOCTEST_MOD = None
# Example:
#DOCTEST_MOD = 'ipython1.tools.utils'

##########################################################################
### Test classes go here

class FooTestCase(unittest.TestCase):
    def test_foo(self):
        pass
        
##########################################################################
### Main
# This ensures that the code will run either standalone as a script, or that
# it can be picked up by the main test wrapper which runs all the tests.
if __name__ == '__main__':
    unittest.main(testLoader=ipdoctest.IPDocTestLoader(__doc__,DOCTEST_MOD))
else:
    testSuite = lambda : ipdoctest.makeTestSuite(__name__,DOCTEST_MOD)
