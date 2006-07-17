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

from twisted.python import components, log
from twisted.spread import pb
from zope.interface import Interface, implements

from ipython1.kernel import controllerservice

# Expose a PB interface to the ControllerService
     
class IPerspectiveController(Interface):
    
    def remote_registerEngine(self, perspectiveEngine):
        """register new engine on controller"""
    
    def remote_submitCommand(self, id, cmd):
        """submitCommand to engine #id"""
    


class PerspectiveControllerFromService(pb.Root):
    
    implements(IPerspectiveController)
    
    def __init__(self, service):
        self.service = service
    
    def remote_registerEngine(self, engineReference):
        id = self.service.registerEngine(engineReference)
        engineReference.broker.notifyOnDisconnect(self.service.engine[id].handleDisconnect)
        return id
    
    #should I separate the two root objects (Remote, Control)?
    def remote_submitCommand(self, id, cmd):
        self.service.engine[id].submitCommmand(cmd)
    
    def remote_testCommands(self, id):
        self.service.testCommands(id)
    


components.registerAdapter(PerspectiveControllerFromService,
                           controllerservice.ControllerService,
                           IPerspectiveController)

