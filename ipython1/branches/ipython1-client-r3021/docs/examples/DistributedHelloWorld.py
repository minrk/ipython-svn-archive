"""
A Distributed Hello world
Ken Kinder <ken@kenkinder.com>
"""
from ipython1.kernel import client

tc = client.TaskController(('127.0.0.1', 10113))
mec = client.MultiEngineController(('127.0.0.1', 10105))

mec.execute('import time')
helloTaskId = tc.run(client.Task('time.sleep(3) ; word = "Hello,"', resultNames=['word']))
worldTaskId = tc.run(client.Task('time.sleep(3) ; word = "World!"', resultNames=['word']))

print tc.getTaskResult(helloTaskId).ns.word, tc.getTaskResult(worldTaskId).ns.word
