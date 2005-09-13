import cPickle as pickle
import sys
from optparse import OptionParser

from twisted.internet import reactor
from twisted.python import log

from kernelcore import KernelTCPFactory

def main(port, allow_ip=None):
    allow_list = ['127.0.0.1']
    if allow_ip is not None:
        allow_list.append(allow_ip)
    log.startLogging(sys.stdout)       
    d = reactor.listenTCP(port, KernelTCPFactory(allow=allow_list))
    reactor.run()
    
if __name__ == "__main__":
    parser = OptionParser()
    parser.set_defaults(port=10105)
    parser.add_option("-p", "--port", type="int", dest="port",
        help="the TCP port the kernel will listen on")
    parser.add_option("-a", "--allow", dest="allow_ip",
        help="an IP address to allow to connect to the kernel")
    (options, args) = parser.parse_args()
    print "Starting the kernel on port %i" % options.port
    main(options.port, options.allow_ip)