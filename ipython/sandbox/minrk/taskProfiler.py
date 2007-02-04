#!/usr/env/python

import random, sys
from optparse import OptionParser

from IPython.genutils import time
from ipython1.kernel import multienginepb, taskpb, task

def main():
    parser = OptionParser()
    parser.set_defaults(n=100)
    parser.set_defaults(t=1)
    parser.set_defaults(T=60)
    parser.set_defaults(controller='localhost')
    parser.set_defaults(meport=10111)
    parser.set_defaults(tport=10114)
    
    parser.add_option("-n", type='int', dest='n')
    parser.add_option("-t", type='int', dest='t')
    parser.add_option("-T", type='int', dest='T')
    parser.add_option("-c", type='string', dest='controller')
    parser.add_option("-p", type='int', dest='meport')
    parser.add_option("-P", type='int', dest='tport')
    
    (opts, args) = parser.parse_args()
    
    rc = multienginepb.PBInteractiveMultiEngineClient((opts.controller, opts.meport))
    rt = taskpb.PBConnectingTaskClient((opts.controller, opts.tport))
    
    rc.connect()
    rt.connect()

    rc.block=True
    nengines = len(rc.getIDs())
    rc.executeAll('from IPython.genutils import time')

    # the jobs should take a random time within a range
    times = [random.random()*(opts.T-opts.t)+opts.t for i in range(opts.n)]
    tasks = [task.Task("time.sleep(%f)"%t) for t in times]
    stime = sum(times)
    
    print "executing %.3f secs on %i engines"%(stime, nengines)
    
    start = time.time()
    results = [rt.run(t) for t in tasks]
    rt.barrier()
    stop = time.time()

    ptime = stop-start
    scale = stime/ptime
    
    print "executed %.3f secs in %.3f secs"%(stime, ptime)
    print "min task time: %.3f"%min(times)
    print "max task time: %.3f"%max(times)
    print "%.3fx parallel performance on %i engines"%(scale, nengines)
    print "%.3f%% of theoretical max"%(scale/nengines)


if __name__ == '__main__':
    main()