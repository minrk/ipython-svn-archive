
"""The Twisted core of the ipython controller.

This module contains the Twisted protocols, factories, etc. used to
implement the ipython controller.  This module only contains the network related
parts of the controller.
"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from twisted.internet import protocol
from twisted.protocols import basic

class ControllerProtocol(basic.LineReceiver):
	"""the controller protocol"""
	pass

class ControllerFactory(protocol.ServerFactory):
	"""the controller factory"""
	protocol = ControllerProtocol
	pass

