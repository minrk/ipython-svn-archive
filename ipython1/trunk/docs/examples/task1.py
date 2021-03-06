from ipython1.kernel import client

tc = client.TaskClient(('127.0.0.1', 10113))
rc = client.MultiEngineClient(('127.0.0.1', 10105))

rc.push(dict(d=30))

cmd1 = """\
a = 5
b = 10*d
c = a*b*d
"""

t1 = client.Task(cmd1, clear_before=False, clear_after=True, pull=['a','b','c'])
tid1 = tc.run(t1)
tr1 = tc.get_task_result(tid1,block=True)
tr1.raiseException()
print "a, b: ", tr1.ns.a, tr1.ns.b