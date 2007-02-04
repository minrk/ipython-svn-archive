#!/usr/env/python

import random, sys
from optparse import OptionParser

from IPython.genutils import time
from ipython1.kernel import multienginepb, taskpb, task

def main():
    parser = OptionParser()
    parser.set_defaults(n=100)
    parser.set_defaults(tmin=1)
    parser.set_defaults(tmax=60)
    parser.set_defaults(controller='localhost')
    parser.set_defaults(meport=10111)
    parser.set_defaults(tport=10114)
    
    parser.add_option("-n", type='int', dest='n',
        help='the number of tasks to run')
    parser.add_option("-t", type='float', dest='tmin', 
        help='the minimum task length in seconds')
    parser.add_option("-T", type='float', dest='tmax',
        help='the maximum task length in seconds')
    parser.add_option("-c", type='string', dest='controller',
        help='the address of the controller')
    parser.add_option("-p", type='int', dest='meport',
        help="the port on which the controller listens for MultiEnginePB")
    parser.add_option("-P", type='int', dest='tport',
        help="the port on which the controller listens for TaskPB")
    
    (opts, args) = parser.parse_args()
    assert opts.tmax >= opts.tmin, "tmax must not be smaller than tmin"
    
    rc = multienginepb.PBInteractiveMultiEngineClient((opts.controller, opts.meport))
    rt = taskpb.PBConnectingTaskClient((opts.controller, opts.tport))
    
    rc.connect()
    rt.connect()

    rc.block=True
    nengines = len(rc.getIDs())
    rc.executeAll('from IPython.genutils import time')

    # the jobs should take a random time within a range
    times = [random.random()*(opts.tmax-opts.tmin)+opts.tmin for i in range(opts.n)]
    tasks = [task.Task("time.sleep(%f)"%t) for t in times]
    stime = sum(times)
    
    print "executing %i tasks, totalling %.1f secs on %i engines"%(opts.n, stime, nengines)
    print "min task time: %.1f"%min(times)
    print "max task time: %.1f"%max(times)
    time.sleep(1)
    start = time.time()
    results = [rt.run(t) for t in tasks]
    rt.barrier()
    stop = time.time()

    ptime = stop-start
    scale = stime/ptime
    
    print "executed %.1f secs in %.1f secs"%(stime, ptime)
    print "%.3fx parallel performance on %i engines"%(scale, nengines)
    print "%.1f%% of theoretical max"%(100*scale/nengines)


if __name__ == '__main__':
    main()