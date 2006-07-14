from twisted.internet import reactor
from ipython1.startup import callback

# Parameters
port = 12001
kernel_count = 4
filename = "myfile.txt"
callbackAddr = ('192.168.0.1',10105)
        
# Server
callbackFactory = callback.CallbackFactory(kernel_count, filename)
server = reactor.listenTCP(port, callbackFactory)
reactor.run()
