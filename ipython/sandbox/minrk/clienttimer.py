#!/usr/bin/ipython
"""timer test for controllerclient"""

import time, sys

from ipython1.kernel.controllerclient import RemoteController

rc = RemoteController(('127.0.0.1', 10105))
rc.connect()
nonblock = ''
block = ''

for i in range(8):
    time.sleep(1)
    start  = time.time()
    rc.execute('c=1', block=True)
    split1 = time.time()
    time.sleep(1)
    split2 = time.time()
    rc.execute('b=2')
    stop = time.time()
    block += "%.0f " %(1000*(split1-start))
    nonblock += "%.0f " %(1000*(stop-split2))


print "block (in ms): ", block
print "nonblock (in ms): ", nonblock

