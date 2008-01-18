import ipython1.kernel.api as kernel

tc = kernel.TaskController(('127.0.0.1', 10113))
rc = kernel.RemoteController(('127.0.0.1', 10105))

rc.pushAll(d=30)

cmd1 = """\
a = 5
b = 10*d
"""

t1 = kernel.Task(cmd1, clearBefore=False, clearAfter=True, resultNames=['a','b','c'])
tid1 = tc.run(t1)
tr1 = tc.getTaskResult(tid1,block=True)
tr1.raiseException()
print "a, b: ", tr1.ns.a, tr1.ns.b