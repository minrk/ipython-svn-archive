#!/usr/bin/env python
"""A standalone script that can contain multiple tests.

In this example, we make a special test object from snakeoil.oilscript.  This
object has an API that allows you to assert failure or success (it encapsulates
all the assertions of a TestCase object, and the Numpy version adds the
assertions from numpy.testing.

If you use this object, each time you call an assertion, it is recorded as a
success if it passes.  If it fails, the failure is recorded and the entire
script stops executing.
"""

# The mkScriptTestManager object allows you to create a test manager object
# with which you can declare success/failures throughout the test.  This is
# useful so that a single script shows up as multiple, independent tests in
# final runs, as well as providing summary information (see the end).

# Note: the oilscript module contains a numpy-enabled version of the same
# object, called mkNumpyScriptTestManager, which exposes the assertions from
# numpy.testing as well.

from snakeoil.oilscript import mkScriptTestManager
test = mkScriptTestManager()

# Once you have your test object, you can declare individual test successes:

for i in range(6):
    test.succeed()

# or make checks
x, y = 1,2
test.assertEquals(x+y,3)

# etc.  The test object exposes all the assertions from unittest.TestCase, in
# addition to the .succeed() method above.

# This method gives you a nice summary printout (test.summary() can be called
# to retrieve the summary as a string).  This method is a no-op when the script
# is run inside a test runner as a unittest, to avoid crowding the test run
# with spurious output (test runners typically summarize the whole run at the
# end). 
test.print_summary()
