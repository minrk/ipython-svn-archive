from twisted.internet import reactor
from ipython1.startup import callback
from twisted.python import log

import sys

# Parameters
port = 12001
kernelCount = 4
filename = "myfile.txt"
        
# Server
callbackFactory = callback.CallbackFactory(kernelCount=kernelCount,
    filename=filename)
server = reactor.listenTCP(port, callbackFactory)
log.startLogging(sys.stdout)
reactor.run()
