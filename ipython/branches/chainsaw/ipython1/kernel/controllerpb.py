# -*- test-case-name: ipython1.test.test_controllerpb -*-
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
from ipython1.kernel.engineservice import IEngine, QueuedEngine
# Root object for remote Engine server factory
    
class IPBRemoteEngineRoot(Interface):
    """Root object for the controller service Remote Engine server factory"""
    
    def remote_registerEngine(self, engineReference):
        """register new engine on controller"""
    

class PBRemoteEngineRootFromService(pb.Root):
    """Perspective Broker Root object adapter for Controller Service 
    Remote Engine connection"""
    implements(IPBRemoteEngineRoot)
    
    def __init__(self, service):
        self.service = service
    
    def remote_registerEngine(self, engineReference, id):
        engine = IEngine(engineReference)
        remoteEngine = QueuedEngine(engine)
        id = self.service.registerEngine(remoteEngine, id)
        e = self.service.engine[id]
        def notify():
            lambda : self.service.disconnectEngine(id)
        engineReference.broker.notifyOnDisconnect(notify)
        return id
    

components.registerAdapter(PBRemoteEngineRootFromService,
                        controllerservice.ControllerService,
                        IPBRemoteEngineRoot)

#root object for control factory
class IPBControlRoot(Interface):
    """the Control PB Root object for the controller service server factory"""
    
    def remote_submitCommand(self, cmd, id='all'):
        """submitCommand to engine #id"""
    
    def remote_tellAll(self, cmd):
        """submit command to all available engines"""
    
    def remote_cleanQueue(self, id='all'):
        """Cleans out pending commands in the kernel's queue."""
    
    def remote_interruptEngine(self, id='all'):
        """Send SIGUSR1 to the kernel engine to stop the current command."""
    

class PBControlRootFromService(pb.Root):
    """Perspective Broker Root object adapter for Controller Service"""
    
    implements(IPBControlRoot)
    
    def __init__(self, service):
        self.service = service
    
    def remote_submitCommand(self, cmd, id='all'):
        """submitCommand to engine #<id>"""
        return self.service.submitCommand(cmd, id)
    
    def remote_tellAll(self, cmd):
        """submit command to all available engine(s)"""
        return self.service.tellAll(cmd)
    
    def remote_cleanQueue(self, id='all'):
        """Cleans out pending commands in the kernel's queue."""
        return self.service.cleanQueue(id)
    
    def remote_interruptEngine(self, id='all'):
        """Send SIGUSR1 to the kernel engine to stop the current command."""
        return self.service.interruptEngine(id)
    

components.registerAdapter(PBControlRootFromService,
                        controllerservice.ControllerService,
                        IPBControlRoot)
