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

from IPython.genutils import get_home_dir

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
        else:
            self.transport.loseConnection()

class CallbackFactory(protocol.ServerFactory):
    protocol = CallbackProtocol
    
    def __init__(self, kernelCount=-1, filename=""):
        self.kernels = []
        self.kernelCount = kernelCount
        self.filename = get_home_dir() + "/.ipython/" + filename
        
    def _writeAddrToFile(self, addr):
        self.actualFile = file(self.filename,'a')
        self.actualFile.write("%s %i\n" % (addr[0], addr[1]))
        self.actualFile.close()
    
    def registerKernel(self,addr):
        log.msg("Kernel found: %s %i" % (addr[0], addr[1]))
        self.kernels.append(addr)
        self._writeAddrToFile(addr)
        if len(self.kernels) == self.kernelCount:
            log.msg("%i kernels have replied, I am going to quit" % \
                len(self.kernels))
            reactor.stop()

    def stopFactory(self):
        pass
        #self.actualFile.close()

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
        #print reason
        if self.tries > 1:
            reactor.callLater(self.delay, connector.connect)
            self.tries -= 1
            
    def startedConnecting(self, connector):
        log.msg("Attempting to callback controller...")


