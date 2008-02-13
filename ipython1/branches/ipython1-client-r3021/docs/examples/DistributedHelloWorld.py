"""
A Distributed Hello world
Ken Kinder <ken@kenkinder.com>
"""
from ipython1.kernel import client

tc = client.TaskController(('127.0.0.1', 10113))
mec = client.MultiEngineController(('127.0.0.1', 10105))

mec.execute('import time')
helloTaskId = tc.run(client.Task('time.sleep(3) ; word = "Hello,"', pull=['word']))
worldTaskId = tc.run(client.Task('time.sleep(3) ; word = "World!"', pull=['word']))

print tc.get_task_result(helloTaskId).ns.word, tc.get_task_result(worldTaskId).ns.word
