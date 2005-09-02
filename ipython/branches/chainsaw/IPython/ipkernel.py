import cPickle as pickle

from twisted.internet import protocol, reactor, threads, defer
from twisted.protocols import basic
from twisted.python.runtime import seconds
from twisted.python import log
from twisted.python import failure
import sys

from ipic import QueuedInteractiveConsole
from ipkernelcore import *

def main(port):
    log.startLogging(sys.stdout)
        
    reactor.suggestThreadPoolSize(5)
        
    d = reactor.listenTCP(port, IPythonTCPFactory(validate=['127.0.0.1']))
    reactor.run()
    
if __name__ == "__main__":
    port = int(sys.argv[1])
    main(port)