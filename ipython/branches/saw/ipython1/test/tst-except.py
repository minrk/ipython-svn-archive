#!/usr/bin/env python
import ipython1.kernel.api as kernel

from ipython1.scripts import ipcluster1 as ipc

# Start controller/engine for testing

controller, engines = ipc.startLocalCluster(n=1)




# Get a remote controller instance
rc = kernel.RemoteController(('127.0.0.1',10105))
print 'IDs:',rc.getIDs()

rc.executeAll('a=[0]')
aa = rc.gatherAll('a')
print "aa=",aa


try:
    rc.executeAll('a[0]')  # OK
    rc.executeAll('a[1]')  # Error
finally:
    ipc.stopCluster(controller,engines)
