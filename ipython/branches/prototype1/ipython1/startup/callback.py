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
from twisted.python import log

class CallbackProtocol(basic.LineReceiver):
        
    def connectionMade(self):
        log.msg("Connection Made")
        
    def lineReceived(self, line):
        split_line = line.split(" ",1)
        if len(split_line) == 2:
            # No ckecking performed to make sure the ip and port are ok
            ip = split_line[0]
            port = int(split_line[1])
            self.sendLine("OK")
            self.factory.registerKernel((ip, port))
            self.transport.loseConnection()
        else:
            self.transport.loseConnection()

class CallbackFactory(protocol.ServerFactory):
    protocol = CallbackProtocol
    
    def __init__(self, kernel_count, filename):
        self.kernels = []
        self.kernel_count = kernel_count
        self.filename = filename
        self.actualFile = file(self.filename,'w')
        
    def _writeAddrToFile(self, addr):
        self.actualFile.write("%s %i\n" % (addr[0], addr[1]))
    
    def registerKernel(self,addr):
        self.kernels.append(addr)
        self._writeAddrToFile(addr)
        if len(self.kernels) == self.kernel_count:
            print "Kernels found, quiting..."
            #self.actualFile.close()
            reactor.stop()

    def stopFactory(self):
        self.actualFile.close()

class CallbackClientProtocol(basic.LineReceiver):
        
    def connectionMade(self):
        (ip, port) = self.factory.getAddress()
        self.sendLine("%s %i" % (ip, port))
        
    def lineReceived(self, line):
        if line == "OK":
            self.transport.loseConnection()
            
class CallbackClientFactory(protocol.ClientFactory):
    protocol = CallbackClientProtocol

    def __init__(self, addr, tries=1, delay=2.0):
        self.addr = addr
        self.tries = tries
        self.delay = 2.0
                
    def getAddress(self):
        return self.addr

    def clientConnectionFailed(self, connector, reason):
        print reason
        if self.tries > 1:
            reactor.callLater(self.delay, connector.connect)
            self.tries -= 1


