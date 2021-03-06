"""An example of how to use IPython1 for plotting remote parallel data

The two files plotting_frontend.ipy and plotting_backend.py go together.

To run this example, first start the IPython controller and 4
engines::

    ipcluster -n 4

Then start ipython in pylab mode::

    ipython -pylab
    
Then a simple "run plotting_frontend.ipy" in IPython will run the
example.  When this is done, all the variables (such as number, downx, etc.)
are available in IPython, so for example you can make additional plots.
"""

import numpy as N
from pylab import *
import ipython1.kernel.api as kernel

# Get an IPython1 client
rc = kernel.RemoteController(('127.0.0.1',10105))
rc.getIDs()

# Run the simulation on all the engines
rc.runAll('plotting_backend.py')

# Bring back the data
number = rc.pullAll('number')
d_number = rc.pullAll('d_number')
downx = rc.gatherAll('downx')
downy = rc.gatherAll('downy')
downpx = rc.gatherAll('downpx')
downpy = rc.gatherAll('downpy')

print "number: ", sum(number)
print "downsampled number: ", sum(d_number)

# Make a scatter plot of the gathered data
# These calls to matplotlib could be replaced by calls to pygist or
# another plotting package.
figure(1)
scatter(downx, downy)
xlabel('x')
ylabel('y')
figure(2)
scatter(downpx, downpy)
xlabel('px')
ylabel('py')
show()