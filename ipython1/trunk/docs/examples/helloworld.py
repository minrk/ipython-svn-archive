"""
A Distributed Hello world
Ken Kinder <ken@kenkinder.com>
"""
from ipython1.kernel import client

tc = client.TaskClient(('127.0.0.1', 10113))
mec = client.MultiEngineClient(('127.0.0.1', 10105))

mec.execute('import time')
hello_taskid = tc.run(client.Task('time.sleep(3) ; word = "Hello,"', pull=('word')))
world_taskid = tc.run(client.Task('time.sleep(3) ; word = "World!"', pull=('word')))
print "Submitted tasks:", hello_taskid, world_taskid
print tc.get_task_result(hello_taskid,block=True).ns.word, tc.get_task_result(world_taskid,block=True).ns.word
