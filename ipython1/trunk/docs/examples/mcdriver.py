#!/usr/bin/env python
# encoding: utf-8
"""Run a Monte-Carlo options pricer in parallel."""

import ipython1.kernel.api as kernel
import numpy as N
from mcpricer import MCOptionPricer


tc = kernel.TaskController(('127.0.0.1', 10113))
rc = kernel.RemoteController(('127.0.0.1', 10105))

# Initialize the common code on the engines
rc.runAll('mcpricer.py')

# Push the variables that won't change (stock print, interest rate, days and MC paths)
rc.pushAll(S=100.0, r=0.05, days=260, paths=10000)

task_string = """\
op = MCOptionPricer(S,K,sigma,r,days,paths)
op.run()
vp, ap, vc, ac = op.vanilla_put, op.asian_put, op.vanilla_call, op.asian_call
"""

# Create arrays of strike prices and volatilities
K_vals = N.arange(90.0,110.0,2.0)
sigma_vals = N.arange(0.02, 0.3, 0.02)

# Submit tasks
taskIDs = []
for K in K_vals:
    for sigma in sigma_vals:
        t = kernel.Task(task_string, 
            setupNS=dict(sigma=sigma,K=K),
            resultNames=['vp','ap','vc','ac','sigma','K'])
        taskIDs.append(tc.run(t))

print "Submitted tasks: ", taskIDs

# Block until tasks are completed
tc.barrier(taskIDs)

# Get the results
results = [tc.getTaskResult(tid) for tid in taskIDs]

# Assemble the result
vc = N.empty(K_vals.shape[0]*sigma_vals.shape[0],dtype='float64')
vp = N.empty(K_vals.shape[0]*sigma_vals.shape[0],dtype='float64')
ac = N.empty(K_vals.shape[0]*sigma_vals.shape[0],dtype='float64')
ap = N.empty(K_vals.shape[0]*sigma_vals.shape[0],dtype='float64')
for i, tr in enumerate(results):
    ns = tr.ns
    vc[i] = ns.vc
    vp[i] = ns.vp
    ac[i] = ns.ac
    ap[i] = ns.ap
vc.shape = (K_vals.shape[0],sigma_vals.shape[0])
vp.shape = (K_vals.shape[0],sigma_vals.shape[0])
ac.shape = (K_vals.shape[0],sigma_vals.shape[0])
ap.shape = (K_vals.shape[0],sigma_vals.shape[0])


def plot_options(K_vals, sigma_vals, prices):
    """Make a contour plot of the option prices."""
    import pylab
    pylab.contourf(sigma_vals, K_vals, prices)
    pylab.colorbar()
    pylab.title("Option Price")
    pylab.xlabel("Volatility")
    pylab.ylabel("Strike Price")
