#!/usr/bin/ipython
"""timer test for controllerclient"""

import time, sys

from ipython1.kernel.controllerclient import RemoteController

rc = RemoteController(('24.6.186.70', 10105))
rc.connect()
nonblock = ''
block = ''
c = 1
b = 2
for i in range(8):
#    time.sleep(1)
#    start  = time.time()
#    rc.execute('c=%i' %c, block=True)
#    split1 = time.time()
    time.sleep(1)
    split2 = time.time()
    rc.execute('b=%i' %b)
    stop = time.time()
#    block += "%.1f " %(1000*(split1-start))
    nonblock += "%.2f " %(1000*(stop-split2))
#    assert(rc.pull('c', 0) is c)
#    assert(rc.pull('b', 0) is b)
#    c+=1
    b+=2

#print "block (in ms): ", block
print "nonblock (in ms): ", nonblock

