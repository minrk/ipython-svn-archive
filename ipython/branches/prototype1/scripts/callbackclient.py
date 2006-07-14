from twisted.internet import reactor
from ipython1.startup import callback

# Parameters
port = 12001
kernel_count = 4
filename = "myfile.txt"
callbackAddr = ('192.168.0.1',10105)

kernelFactories = []
for k in range(kernel_count):
    kf = callback.CallbackClientFactory(callbackAddr, tries=5)
    kfConnector = reactor.connectTCP("127.0.0.1", port, kf)
    kernelFactories.append(kfConnector)
reactor.run()
