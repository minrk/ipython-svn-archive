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
from tcommon import *

# If you have standalone doctests in a separate file, set their names in the
# dt_files variable (as a single string  or a list thereof):
dt_files = ['tst_tools_utils_doctest.txt',
            'tst_tools_utils_doctest2.txt']

# If you have any modules whose docstrings should be scanned for embedded tests
# as examples accorging to standard doctest practice, set them here (as a
# single string or a list thereof):
dt_modules = 'ipython1.tools.utils'

##########################################################################
### Regular unittest test classes go here

class FooTestCase(unittest.TestCase):
    def test_foo(self):
        pass
        
##########################################################################
### Main
# This ensures that the code will run either standalone as a script, or that it
# can be picked up by Twisted's `trial` test wrapper to run all the tests.

if __name__ == '__main__':
    unittest.main(testLoader=IPDocTestLoader(dt_files,dt_modules))
else:
    testSuite = lambda : makeTestSuite(__name__,dt_files,dt_modules)
