#!/usr/bin/env python
# encoding: utf-8

from ipython1.kernel import client
import time

tc = client.TaskClient(('127.0.0.1', 10113))
mec = client.MultiEngineClient(('127.0.0.1', 10105))

mec.execute('import time')

for i in range(24):
    tc.irun('time.sleep(1)')

for i in range(6):
    time.sleep(1.0)
    print "Queue status (vebose=False)"
    print tc.queue_status()
    
for i in range(24):
    tc.irun('time.sleep(1)')

for i in range(6):
    time.sleep(1.0)
    print "Queue status (vebose=True)"
    print tc.queue_status(True)

for i in range(12):
    tc.irun('time.sleep(2)')

print "Queue status (vebose=True)"
print tc.queue_status(True)

qs = tc.queue_status(True)
sched = qs['scheduled']

for tid in sched[-4:]:
    tc.abort(tid)

for i in range(6):
    time.sleep(1.0)
    print "Queue status (vebose=True)"
    print tc.queue_status(True)

