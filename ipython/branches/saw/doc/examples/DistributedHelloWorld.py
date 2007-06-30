"""
A Distributed Hello world
Ken Kinder <ken@kenkinder.com>
"""
import ipython1.kernel.api as kernel
import ipython1.kernel.multienginexmlrpc
import ipython1.kernel.taskxmlrpc

rc = kernel.TaskController(('127.0.0.1', 10113))
ipc = kernel.RemoteController(('127.0.0.1', 10105))
assert isinstance(rc, ipython1.kernel.taskxmlrpc.XMLRPCInteractiveTaskClient)
assert isinstance(ipc, ipython1.kernel.multienginexmlrpc.XMLRPCInteractiveMultiEngineClient)

ipc.execute('all', 'import time')
helloTaskId = rc.run(kernel.Task('time.sleep(3) ; word = "Hello,"', resultNames=['word']))
worldTaskId = rc.run(kernel.Task('time.sleep(3) ; word = "World!"', resultNames=['word']))

print rc.getTaskResult(helloTaskId).ns.word, rc.getTaskResult(worldTaskId).ns.word
