import sys

from twistbonjour import BonjourAdvertiser
from twisted.internet import reactor, protocol
from twisted.python import log

class Echo(protocol.Protocol):
    """This is just about the simplest possible protocol"""
    
    def dataReceived(self, data):
        "As soon as any data is received, write it back."
        self.transport.write(data)

class BonjourEchoFactory(protocol.ServerFactory):
    """A factory with Bonjour support added.
    
    This Factory class shows how to advertise with Bonjour.  The classes
    used here don't necessarily have to be used in a Factory like this, but
    this is one way to go about it.  It probably makes more sense to not mix        
    Bonjour into the protocol's Factory, but it works.
    
    The Bonjour stuff is done by overriding startFactory as seen below.
    """
    protocol = Echo
    
    def __init__(self, serviceName):
        self.serviceName = serviceName
        
    def stopAdvertising(self):
        self.ba.stopAdvertising()
        
    def startFactory(self):
        self.ba = BonjourAdvertiser(self.serviceName,
                                    "_echo._tcp",
                                    8000,
                                    reactor)
                                    
        d = self.ba.startAdvertising()
        
        def didAdvertise(t):
            print "Advertising with Bonjour:", t['name'], \
                t['regtype'], t['domain']
        def didNotAdvertise(t):
            t.printTraceback()
        d.addCallback(didAdvertise)
        d.addErrback(didNotAdvertise)
        
def main():
    """This runs the protocol on port 8000"""
    log.startLogging(sys.stdout)    
    factory = BonjourEchoFactory("myecho")
    reactor.listenTCP(8000,factory)
    reactor.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()
