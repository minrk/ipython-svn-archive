# Setup - all imports are done in tcommon
from ipython1.testutils import tcommon
from ipython1.testutils.tcommon import *

# Doctest code begins here
from ipython1.tools import utils

for i in range(10):
    print i,
    print i+1

print 'simple loop is over'
