"""perspective broker engine factory from kernel2p.kernelpb"""
"""Expose the IPython Kernel Service using Twisted's Perspective Broker.

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

from ipython1.kernel import engineservice

# Expose a PB interface to the EngineService
     
class IPerspectiveEngine(Interface):

    def remoteExecute(self, lines):
        """Execute lines of Python code."""
    
    def remotePut(self, key, value):
        """Put value into locals namespace with name key."""
        
    def remotePutPickle(self, key, package):
        """Unpickle package and put into the locals namespace with name key."""
        
    def remoteGet(self, key):
        """Gets an item out of the self.locals dict by key."""

    def remoteGetPickle(self, key):
        """Gets an item out of the self.locals dist by key and pickles it."""

    def remoteReset(self):
        """Reset the InteractiveShell."""
        
    def remoteGetCommand(self, i=None):
        """Get the stdin/stdout/stderr of command i."""

    def remoteGetLastCommandIndex(self):
        """Get the index of the last command."""

    def remoteRestartEngine(self):
        """Stops and restarts the kernel engine process."""
        
    def remoteCleanQueue(self):
        """Cleans out pending commands in the kernel's queue."""
        
    def remoteInterruptEngine(self):
        """Send SIGUSR1 to the kernel engine to stop the current command."""

class PerspectiveEngineFromService(pb.Root):

    implements(IPerspectiveEngine)

    def __init__(self, service):
        self.service = service

    def remoteExecute(self, lines):
        return self.service.execute(lines)
    
    def remotePut(self, key, value):
        return self.service.put(key, value)
        
    def remotePutPickle(self, key, package):
        return self.service.put_pickle(key, package)
        
    def remoteGet(self, key):
        return self.service.get(key)

    def remoteGetPickle(self, key):
        return self.service.get_pickle(key)

    def remoteReset(self):
        return self.service.reset()
        
    def remoteGetCommand(self, i=None):
        return self.service.get_command(i)

    def remoteGetLastCommandIndex(self):
        return self.service.get_last_command_index()

    def remoteRestartEngine(self):
        return self.service.restart_engine()
        
    def remoteCleanQueue(self):
        return self.service.clean_queue()

    def remoteInterruptEngine(self):
        return self.service.interrupt_engine()
    
components.registerAdapter(PerspectiveEngineFromService,
                           engineservice.EngineService,
                           IPerspectiveEngine)
    
    
    
