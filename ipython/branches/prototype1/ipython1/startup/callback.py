"""A protocol for kernels to callback to a controller."""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <ellisonbg@gmail.com>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from twisted.internet import protocol, reactor, defer
from twisted.protocols import basic

class CallbackProtocol(basic.LineReceiver):
        
    def lineReceived(self, line):
        split_line = line.split(" ",1)
        if len(split_line) == 2:
            # No ckecking performed to make sure the ip and port are ok
            ip = split_line[0]
            port = int(split_line[1])
            self.sendLine("OK")
            self.factory.registerKernel((ip, port))
            self.transport.loseConnection()
        elif:
            self.transport.loseConnection()

class CallbackFactory(protocol.ServerFactory):
    protocol = CallbackProtocol
    
    def __init__(self, kernel_count, filename):
        self.kernels = []
        self.kernel_count = kernel_count
        self.filename = filename
        
    def _writeKernelsToFile(self):
        print self.kernels
    
    def registerKernel(self,addr):
        self.kernels.append(addr)
        self._writeKernelsToFile()
        if len(self.kernels) == self.kernel_count:
            reactor.stop()

class CallbackClientProtocol(basic.LineReceiver):
        
    def connectionMade(self):
        (ip, port) = self.factory.getAddress()
        self.selfLine("%s %i" % (self.ip, self.port))
        
    def lineReceived(self, line):
        if line == "OK":
            self.transport.loseConnection()
            
class CallbackClientFactory(protocol.ClientFactory):
    protocol = CallbackClientProtocol

    def __init__(self, addr, tries=1, delay=2.0)
        self.addr = addr
        self.tries = tries
        self.delay = 2.0
                
    def getAddress(self):
        return self.addr

    def clientConnectionFailed(self, connector, reason):
        if tries > 1:
            reactor.callLater(delay, connector.connect)
            tries -= 1


