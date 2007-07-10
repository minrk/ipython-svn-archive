"""Example of how to use pylab to plot parallel data.

The idea here is to run matplotlib is the same IPython session
as an ipython RemoteController client.  That way matplotlib
can be used to plot parallel data that is gathered using
RemoteController.  

To run this example, first start the IPython controller and 4
engines::

    ipcluster -n 4

Then start ipython in pylab mode::

    ipython -pylab
    
Then a simple "run parallel_pylab.ipy" in IPython will run the
example. 
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
scatter(downx, downy)
