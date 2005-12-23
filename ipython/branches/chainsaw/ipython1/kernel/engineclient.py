"""The Twisted related parts of the kernel engine client."""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************
import cPickle as pickle

from twisted.internet import protocol, reactor, threads, defer
from twisted.protocols import basic
from twisted.python.runtime import seconds
from twisted.python import log
from twisted.python import failure
import sys

class KernelEngineClientProtocol(basic.LineReceiver):
    """Client network protocol for the kernel engine."""
    pass
    
class KernelEngineClientFactoy(protocol.ClientFactory):
    """Client factory for creating KernelEngineClientProtocol instances."""
    pass