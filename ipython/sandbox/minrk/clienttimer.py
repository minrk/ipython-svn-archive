#!/usr/bin/ipython
"""timer test for controllerclient"""

import time, sys
from StringIO import StringIO

#from twisted.python import log
from ipython1.kernel.controllerclient import RemoteController

swapStream = StringIO()
def swap():
    global swapStream
    tmp = sys.stdout
    sys.stdout = swapStream
    swapStream = tmp

tests = 8
failures = []

rc = RemoteController(('127.0.0.1', 10105))
rc.connect()

n = len(rc.status().keys())
timer = max(n/32, .1)

if 'log' in sys.argv:
    logfile = open('%03.fnodeTimerTest.txt' %n, 'a')
    stdout = sys.stdout
    sys.stdout = logfile

print "Running Timing Tests on %i Nodes" %n
print "will run each test %i times" %tests
print
print "all times given in ms"
print

cmd = 'a=5'
print "Non Blocking Execute %s: " %cmd
try:
    for i in range(tests):
        time.sleep(timer)
        start = time.time()
        assert(rc.execute(cmd))
        stop = time.time()
        print "%.2f" %(1000*(stop - start)),
except AssertionError:
    raise
except Exception, e:
    failures.append(e)
print

print "Non Blocking Execute with notify %s: " %cmd
try:
    assert(rc.notify())
    for i in range(tests):
        time.sleep(timer)
        start = time.time()
        assert(rc.execute(cmd))
        stop = time.time()
        print "%.2f" %(1000*(stop - start)),
    time.sleep(timer)
    assert(rc.notify(flag=False))
except AssertionError:
    raise
except Exception, e:
    failures.append(e)
print

print "Blocking Execute %s: " %cmd
try:
    for i in range(tests):
        time.sleep(timer)
        swap()
        start = time.time()
        assert(rc.execute(cmd, block=True))
        stop = time.time()
        swap()
        print "%.2f" %(1000*(stop - start)),
except AssertionError:
    raise
except Exception, e:
    failures.append(e)
print

print "Blocking Execute with Notify %s: " %cmd
try:
    assert(rc.notify())
    for i in range(tests):
        time.sleep(timer)
        swap()
        start = time.time()
        assert(rc.execute(cmd, block=True))
        stop = time.time()
        swap()
        print "%.2f" %(1000*(stop - start)),
    assert(rc.notify(flag=False))
except AssertionError:
    raise
except Exception, e:
    failures.append(e)
print

key = 'a'
value = 'fun'
print "Pushing %s = %s: " %(key, value)
try:
    for i in range(tests):
        time.sleep(timer)
        start = time.time()
        assert(rc.push(key, value))
        stop = time.time()
        print "%.2f" %(1000*(stop - start)),
    time.sleep(timer)
except AssertionError:
    raise
except Exception, e:
    failures.append(e)
print

print "Pulling %s: " %(key)
try:
    for i in range(tests):
        time.sleep(timer)
        start = time.time()
        assert(rc.pull(key) or n is 0)
        stop = time.time()
        print "%.2f" %(1000*(stop - start)),
    time.sleep(timer)
except AssertionError:
    raise
except Exception, e:
    failures.append(e)
print

dikt = {'a':2, 'b':'123'}
print "Updating with %s: " %dikt
try:
    for i in range(tests):
        time.sleep(timer)
        start = time.time()
        assert(rc.update(dikt))
        stop = time.time()
        print "%.2f" %(1000*(stop - start)),
    time.sleep(timer)
except AssertionError:
    raise
except Exception, e:
    failures.append(e)
print

print "Getting Last Command: "
try:
    for i in range(tests):
        time.sleep(timer)
        start = time.time()
        assert(rc.getCommand() or n is 0)
        stop = time.time()
        print "%.2f" %(1000*(stop - start)),
    time.sleep(timer)
except AssertionError:
    raise
except Exception, e:
    failures.append(e)
print

print "Getting Last Command Index: "
try:
    for i in range(tests):
        time.sleep(timer)
        start = time.time()
        assert(rc.getLastCommandIndex() or n is 0)
        stop = time.time()
        print "%.2f" %(1000*(stop - start)),
    time.sleep(timer)
except AssertionError:
    raise
except Exception, e:
    failures.append(e)
print

print "Resetting: "
try:
    for i in range(tests):
        time.sleep(timer)
        start = time.time()
        assert(rc.reset())
        stop = time.time()
        print "%.2f" %(1000*(stop - start)),
    time.sleep(timer)
except AssertionError:
    raise
except Exception, e:
    failures.append(e)
print

print "Getting Status: "
try:
    for i in range(tests):
        time.sleep(timer)
        start = time.time()
        assert(rc.status() or n is 0)
        stop = time.time()
        print "%.2f" %(1000*(stop - start)),
    time.sleep(timer)
except AssertionError:
    raise
except Exception, e:
    failures.append(e)
print

print "Killing: "
try:
    for i in range(tests):
        time.sleep(timer)
        start = time.time()
        assert(rc.kill())
        stop = time.time()
        print "%.2f" %(1000*(stop - start)),
    time.sleep(timer)
except AssertionError:
    raise
except Exception, e:
    failures.append(e)
print

if not failures:
    print "\nSUCCESS!"
else:
    for e in failures:
        raise e
    print "FAILED!"
