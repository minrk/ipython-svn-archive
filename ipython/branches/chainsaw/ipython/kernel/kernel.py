"""The basic ipython computational kernel.

This module is meant to be run from the command line.  To start the kernel,
issue the command:

    python kernel.py

This will start the kernel listening on port 10105 (the default) and will allow
connections from only the localhost (127.0.0.1).  Here is an example that starts
the kernel on port 10106 and allows connections from the localhost and 
121.122.123.124:

    python kernel.py -p 10106 -a 121.122.123.124

For more information on the command line options, run:

    python kernel.py -h

NOTE:  The kernel cannot currently be run in the background, so:

    python kernel.py &

won't result in a running kernel instance.
"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import cPickle as pickle
import sys
from optparse import OptionParser

from twisted.internet import reactor
from twisted.python import log

try:
    from ipython.kernel.kernelcore import KernelTCPFactory
except ImportError:
    from kernel.kernelcore import KernelTCPFactory

#from kernelcore import KernelTCPFactory

def main(port, allow_ip):
    allow_list = ['127.0.0.1']
    if allow_ip is not None:
        allow_list.append(allow_ip)
    log.startLogging(sys.stdout)       
    d = reactor.listenTCP(port, KernelTCPFactory(allow=allow_list))
    reactor.run()

def start(port=10105):
    parser = OptionParser()
    parser.set_defaults(port=port)
    parser.add_option("-p", "--port", type="int", dest="port",
        help="the TCP port the kernel will listen on")
    parser.add_option("-a", "--allow", dest="allow_ip",
        help="an IP address to allow to connect to the kernel")
    (options, args) = parser.parse_args()
    print "Starting the kernel on port %i" % options.port
    main(options.port, options.allow_ip)
    
if __name__ == "__main__":
    start()
