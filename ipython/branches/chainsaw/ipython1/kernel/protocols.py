from twisted.protocols import basic

class EnhancedNetstringReceiver(basic.NetstringReceiver):
    
    def sendBuffer(self, buf):
        bufLength = len(buf)
        self.transport.write('%d:')
        self.transport.write(buf)
        self.transport.write(',')