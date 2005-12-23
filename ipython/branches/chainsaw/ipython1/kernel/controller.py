"""The Twisted related parts of the Kernel Controller.
"""
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

class KernelControllerProtocol(basic.LineReceiver):
    """Network protocol for the kernel controller.
    """
    pass
    
class KernelControllerFactory(protocol.ServerFactory):
    """Factory for creating KernelControllerProtocol instances."""
    pass
