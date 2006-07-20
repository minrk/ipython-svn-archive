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

# Expose a PB interface to the ControllerService
    
class IRemoteEngineRoot(Interface):
    """Root object for the controller service Remote Engine server factory"""
    
    def remote_registerEngine(self, engineReference):
        """register new engine on controller"""
    
    def remote_reconnectEngine(self, id, engineReference):
        """reconnect an engine"""
        
    def remote_setRestart(self, id, s):
        """set state of remote engine id"""
    

class IControlRoot(Interface):
    """the Control Root for the controller service server factory"""
    
    def remote_submitCommand(self, cmd, id=None):
        """submitCommand to engine #id"""
    
    def remote_restartEngine(self, id=None):
        """Stops and restarts the kernel engine process."""
    
    def remote_cleanQueue(self, id=None):
        """Cleans out pending commands in the kernel's queue."""
    
    def remote_interruptEngine(self, id=None):
        """Send SIGUSR1 to the kernel engine to stop the current command."""
    


class RemoteEngineRoot(pb.Root):
    
    implements(IRemoteEngineRoot)
    
    def __init__(self, service):
        self.service = service
    
    def remote_registerEngine(self, engineReference):
        id = self.service.registerEngine(engineReference)
        e = self.service.engine[id]
        engineReference.broker.notifyOnDisconnect(e.handleDisconnect)
        return (id, e.restart)
    
    def remote_reconnectEngine(self, id, engineReference):
        d = self.service.reconnectEngine(id, engineReference)
        e = self.service.engine[id]
        engineReference.broker.notifyOnDisconnect(e.handleDisconnect)
        return d
    
    def remote_setState(self, id, s):
        return self.service.engine[id].setLocalState(s)
    
    

class ControlRoot(pb.Root):
    """the Control Root for the controller service server factory"""
    
    implements(IControlRoot)
    
    def __init__(self, service):
        self.service = service
    
    def remote_submitCommand(self, cmd, id=None):
        """submitCommand to engine #<id>"""
        return self.service.submitCommand(cmd, id)
    
    def remote_restartEngine(self, id=None):
        """Stops and restarts the kernel engine process."""
        return self.service.restartEngine(id)
    
    def cleanQueue(self, id=None):
        """Cleans out pending commands in the kernel's queue."""
        return self.service.cleanQueue(id)
    
    def interruptEngine(self, id=None):
        """Send SIGUSR1 to the kernel engine to stop the current command."""
        return self.service.interruptEngine(id)
    

components.registerAdapter(RemoteEngineRoot,
                        controllerservice.ControllerService,
                        IRemoteEngineRoot)

components.registerAdapter(ControlRoot,
                        controllerservice.ControllerService,
                        IControlRoot)

