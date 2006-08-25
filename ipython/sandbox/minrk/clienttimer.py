#!/usr/local/bin/python
"""timer test for controllerclient"""

import time, sys
from optparse import OptionParser
from StringIO import StringIO
from math import sqrt

from ipython1.kernel.controllerclient import RemoteController

swapStream = StringIO()
def swap():
    global swapStream
    tmp = sys.stdout
    sys.stdout = swapStream
    swapStream = tmp

def main(host, port, tests, timer):
    failures = []
    
    rc = RemoteController((host, port))
    rc.connect()
    
    n = len(rc.getIDs())
    if timer is None:
        timer = max(sqrt(n)/6, 1)
    
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
            assert(rc.execute('all', cmd))
            stop = time.time()
            print "%.2f" %(1000*(stop - start)),
    except AssertionError, e:
        print "Command Failed"
        failures.append(e)
    print
    
    print "Non Blocking Execute with notify %s: " %cmd
    try:
        assert(rc.notify())
        for i in range(tests):
            time.sleep(timer)
            start = time.time()
            assert(rc.execute('all', cmd))
            stop = time.time()
            print "%.2f" %(1000*(stop - start)),
        time.sleep(timer)
        assert(rc.notify(flag=False))
    except AssertionError, e:
        print "Command Failed"
        failures.append(e)
    print
    
    print "Blocking Execute %s: " %cmd
    try:
        for i in range(tests):
            time.sleep(timer)
            swap()
            start = time.time()
            assert(rc.execute('all', cmd, block=True))
            stop = time.time()
            swap()
            print "%.2f" %(1000*(stop - start)),
    except AssertionError, e:
        print "Command Failed"
        failures.append(e)
    print
    
    print "Blocking Execute with Notify %s: " %cmd
    try:
        assert(rc.notify())
        for i in range(tests):
            time.sleep(timer)
            swap()
            start = time.time()
            assert(rc.execute('all', cmd, block=True))
            stop = time.time()
            swap()
            print "%.2f" %(1000*(stop - start)),
        assert(rc.notify(flag=False))
    except AssertionError, e:
        print "Command Failed"
        failures.append(e)
    print
    
    key = 'a'
    value = 'fun'
    print "Pushing %s = %s: " %(key, value)
    try:
        for i in range(tests):
            time.sleep(timer)
            start = time.time()
            assert(rc.push('all', key=value))
            stop = time.time()
            print "%.2f" %(1000*(stop - start)),
        time.sleep(timer)
    except AssertionError, e:
        print "Command Failed"
        failures.append(e)
    print
    
    print "Pulling %s: " %(key)
    try:
        for i in range(tests):
            time.sleep(timer)
            start = time.time()
            assert(rc.pull('all', key) or n is 0)
            stop = time.time()
            print "%.2f" %(1000*(stop - start)),
        time.sleep(timer)
    except AssertionError, e:
        print "Command Failed"
        failures.append(e)
    print
    
    print "Getting Last Command: "
    try:
        for i in range(tests):
            time.sleep(timer)
            start = time.time()
            assert(rc.getResult('all') or n is 0)
            stop = time.time()
            print "%.2f" %(1000*(stop - start)),
        time.sleep(timer)
    except AssertionError, e:
        print "Command Failed"
        failures.append(e)
    print
    
    print "Resetting: "
    try:
        for i in range(tests):
            time.sleep(timer)
            start = time.time()
            assert(rc.reset('all'))
            stop = time.time()
            print "%.2f" %(1000*(stop - start)),
        time.sleep(timer)
    except AssertionError, e:
        print "Command Failed"
        failures.append(e)
    print
    
    print "Getting Status: "
    try:
        for i in range(tests):
            time.sleep(timer)
            start = time.time()
            assert(rc.status('all') or n is 0)
            stop = time.time()
            print "%.2f" %(1000*(stop - start)),
        time.sleep(timer)
    except AssertionError, e:
        print "Command Failed"
        failures.append(e)
    print
    
    print "Killing: "
    try:
        for i in range(tests):
            time.sleep(timer)
            start = time.time()
            assert(rc.kill('all'))
            stop = time.time()
            print "%.2f" %(1000*(stop - start)),
        time.sleep(timer)
    except AssertionError, e:
        print "Command Failed"
        failures.append(e)
    print
    
    if not failures:
        print "\nSUCCESS!"
    else:
        for e in failures:
            raise e
        print "FAILED!"

def start():
    parser = OptionParser()
    parser.set_defaults(port=10105)
    parser.set_defaults(host='127.0.0.1')
    parser.set_defaults(rport=10104)
    parser.set_defaults(results='127.0.0.1')
    parser.set_defaults(tests=8)
    parser.set_defaults(sleep=None)
    
    parser.add_option("-p", "--port", type="int", dest="port",
        help="the TCP port the controller listens on")
    parser.add_option("-c", "--controller", type="str", dest="host",
        help="the ip address of the controller")
    parser.add_option("-R", "--resultport", type="int", dest="rport",
        help="the TCP port the results gathere listens on")
    parser.add_option("-r", "--results", type="str", dest="results",
        help="the ip address of the results gatherer")
    parser.add_option("-n", "--tests", type="int", dest="tests",
        help="the number of times to run each test")
    parser.add_option("-s", "--sleep", type="int", dest="sleep",
        help="the time to sleep between each test (in seconds)")
    (options, args) = parser.parse_args()
    main(options.host, options.port, options.tests, options.sleep)

if __name__ == '__main__':
    start()
