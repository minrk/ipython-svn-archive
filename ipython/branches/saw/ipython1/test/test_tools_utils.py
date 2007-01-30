#!/usr/bin/env python
"""Testing script for the tools.utils module.
"""

# Module imports
import tcommon

# WARNING: do NOT put a reload(tcommon) here!!!  It screws up running of the
# combined test suites by leaving multiple copies of the tcommon module in
# memory.  The resulting errors are extremely strange.

from tcommon import *

# If you have standalone doctests in a separate file, set their names in the
# doctest_files variable (a single string  or 

doctest_files = 'tst_tools_utils_doctest.txt'

# If you have any module whose docstrings should be scanned for embedded tests
# as examples (accorging to standard doctest practice), set it here:
doctest_modules = 'ipython1.tools.utils'

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
    unittest.main(testLoader=ipdoctest.IPDocTestLoader(doctest_files,
                                                       doctest_modules))
else:
    testSuite = lambda : ipdoctest.makeTestSuite(__name__,
                                                 doctest_files,
                                                 doctest_modules)
