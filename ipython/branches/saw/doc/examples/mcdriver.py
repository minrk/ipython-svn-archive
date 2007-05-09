#!/usr/bin/env python
# encoding: utf-8
"""Run a Monte-Carlo options pricer in parallel."""

import ipython1.kernel.api as kernel
import numpy as N
from mcpricer import MCOptionPricer


tc = kernel.TaskController(('127.0.0.1', 10113))
rc = kernel.RemoteController(('127.0.0.1', 10105))

# Initialize the common code
rc.runAll('mcpricer.py')

# Send the variables that won't change
rc.pushAll(S=100.0, K=100.0, sigma=0.25, r=0.05, days=260, paths=10000)

task_string = """op = MCOptionPricer(S,K,sigma,r,days,paths)
op.run()
vp, ap, vc, ac = op.vanilla_put, op.asian_put, op.vanilla_call, op.asian_call
"""

sigmas = N.arange(0.01, 0.3, 0.01)
print sigmas
taskIDs = []
for s in sigmas:
    t = kernel.Task(task_string, setupNS={'sigma':s}, resultNames=['vp','ap','vc','ac','sigma'])
    taskIDs.append(tc.run(t))

tc.barrier(taskIDs)

for tid in taskIDs:
    print tc.getTaskResult(tid)

vp = N.zeros(len(sigmas),dtype='float64')
ap = N.zeros(len(sigmas),dtype='float64')
vc = N.zeros(len(sigmas),dtype='float64')
ac = N.zeros(len(sigmas),dtype='float64')
for i, tid in enumerate(taskIDs):
    tr = tc.getTaskResult(tid)[1]
    vp[i] = tr['vp']
    ap[i] = tr['ap']
    vc[i] = tr['vc']
    ac[i] = tr['ac']

