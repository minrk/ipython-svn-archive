"""perspective broker controller from kernel2p.kernelpb"""
"""Expose the IPython Controller Service using Twisted's Perspective Broker.

This module specifies the IPerspectiveKenel Interface and its implementation
as an Adapter from the IKernelService Interface.  This adapter wraps
KernelService instance into something that inherits from pd.Root.  This makes
is callable using Perspective Broker.

Any public methods of the IKernelService Interface that should be available over
PB must be added to both the Interface and Adapter in this file.

This module must be imported in its entirety to have its Adapters registered
properly:

from ipython1.kernel import enginepb
"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from twisted.python import components
from twisted.spread import pb
from zope.interface import Interface, implements

from ipython1.kernel import controllerservice

# Expose a PB interface to the EngineService
     
class IPerspectiveController(Interface):
    
    def remote_registerEngine(self, protocol):
        """register new engine on controller"""
    
    def remote_getEngineReference(self, engine):
        """get Engine Referenceable object"""
    

class PerspectiveControllerFromService(pb.Root):
    
    implements(IPerspectiveController)
    
    def __init__(self, service):
        self.service = service
    
    def remote_registerEngine(self, protocol=None):
        """register new engine on controller"""
        self.id = self.service.registerEngine(protocol)
        return self.id
    
    def remote_getPerspectiveEngine(self, engine):
        """get Engine Referenceable object"""
        self.perspectiveEngine = engine


components.registerAdapter(PerspectiveControllerFromService,
                           controllerservice.ControllerService,
                           IPerspectiveController)
