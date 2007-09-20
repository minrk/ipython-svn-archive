import time

tstart = time.time()

from ipython1.testutils.tcommon import *
from ipython1.core.interpreter import Interpreter
from ipython1.kernel import api

# Uncomment these using the namespace versions
from ipython1.kernel.scripts.ipengine import *
from ipython1.kernel.scripts.ipcontroller import *
from ipython1.kernel.scripts.ipcluster import *
from ipython1.notebook.scripts.ipnotebook import *

# Uncomment these for the regular saw versioni
# from ipython1.scripts.ipengine import *
# from ipython1.scripts.ipcontroller import *
# from ipython1.scripts.ipcluster import *
# from ipython1.scripts.ipnotebook import *

tstop = time.time()
print "Import time: ", tstop - tstart