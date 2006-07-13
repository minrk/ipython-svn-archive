"""The Interfaces for ipython network components.
    classes:
        IControlProtocol
        IControlFactory
        IREProtocol
        IREFactory
        IEngineProtocol
        IEngineFactory
"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from zope.interface import Interface

#interfaces for Controller network components
class IControlProtocol(Interface):
    pass
class IControlFactory(Interface):
    pass
class IREProtocol(Interface):
    def registerEngine(self, protocol):
        """registerEngine to service"""
class IREFactory(Interface):
    def registerEngine(self, protocol):
        """registerEngine to service"""

#interfaces for Engine network components
class IEngineProtocol(Interface):
    pass
class IEngineFactory(Interface):
    pass
