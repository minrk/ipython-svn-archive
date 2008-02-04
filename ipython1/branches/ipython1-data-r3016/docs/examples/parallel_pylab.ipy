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
rc.activate()

# Create random arrays on the engines
# This is to simulate arrays that you have calculated in parallel
# on the engines.
# Anymore that length 10000 arrays, matplotlib starts to be slow
%px import numpy as N
%px x = N.random.standard_normal(10000)
%px y = N.random.standard_normal(10000)

%px print x[0:10]
%px print y[0:10]

# Bring back the data
x_local = rc.gatherAll('x')
y_local = rc.gatherAll('y')

# Make a scatter plot of the gathered data
scatter(x_local, y_local)
