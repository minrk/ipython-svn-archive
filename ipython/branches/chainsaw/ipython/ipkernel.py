import cPickle as pickle
import sys

from twisted.internet import reactor
from twisted.python import log

from ipkernelcore import IPythonTCPFactory

def main(port):
    log.startLogging(sys.stdout)
        
    reactor.suggestThreadPoolSize(5)
        
    d = reactor.listenTCP(port, IPythonTCPFactory(validate=['127.0.0.1']))
    reactor.run()
    
if __name__ == "__main__":
    port = int(sys.argv[1])
    main(port)