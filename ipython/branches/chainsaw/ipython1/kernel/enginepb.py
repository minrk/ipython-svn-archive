"""perspective broker engine from kernel2p.kernelpb"""
"""Expose the IPython Kernel Service using Twisted's Perspective Broker.

This module specifies the IPerspectiveEngine Interface and its implementation
as an Adapter from the IEngineService Interface.  This adapter wraps
EngineService instance into something that inherits from pb.Referenceable.  This makes
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

from ipython1.kernel import engineservice

# Expose a PB interface to the EngineService
     
class IPerspectiveEngine(Interface):
    
    def remote_execute(self, lines):
        """Execute lines of Python code."""
    
    def remote_put(self, key, value):
        """Put value into locals namespace with name key."""
    
    def remote_put_pickle(self, key, package):
        """Unpickle package and put into the locals namespace with name key."""
    
    def remote_get(self, key):
        """Gets an item out of the self.locals dict by key."""
    
    def remote_get_pickle(self, key):
        """Gets an item out of the self.locals dist by key and pickles it."""
    
    def remote_reset(self):
        """Reset the InteractiveShell."""
    
    def remote_get_command(self, i=None):
        """Get the stdin/stdout/stderr of command i."""
    
    def remote_get_last_command_index(self):
        """Get the index of the last command."""
    
    def remote_restart_engine(self):
        """Stops and restarts the kernel engine process."""
    
    def remote_clean_queue(self):
        """Cleans out pending commands in the kernel's queue."""
    
    def remote_interrupt_engine(self):
        """Send SIGUSR1 to the kernel engine to stop the current command."""
    

class PerspectiveEngineFromService(pb.Referenceable):
    
    implements(IPerspectiveEngine)
    
    def __init__(self, service):
        self.service = service
        self.id = None
    
    def _connect(self, obj):
        self.root = obj
        return self.root.callRemote('registerEngine', self).addCallbacks(self._gotId, self._failure)
    
    def _failure(self, reason):
        raise reason
    
    def _gotId(self, id):
        self.id = id
        log.msg("got ID: %r" %id)
        return id
    
    def remote_execute(self, lines):
        return self.service.execute(lines)
    
    def remote_put(self, key, value):
        return self.service.put(key, value)
    
    def remote_put_pickle(self, key, package):
        return self.service.put_pickle(key, package)
    
    def remote_get(self, key):
        return self.service.get(key)
    
    def remote_get_pickle(self, key):
        return self.service.get_pickle(key)
    
    def remote_reset(self):
        return self.service.reset()
    
    def remote_get_command(self, i=None):
        return self.service.get_command(i)
    
    def remote_get_last_command_index(self):
        return self.service.get_last_command_index()
    
    def remote_restart_engine(self):
        return self.service.restart_engine()
    
    def remote_clean_queue(self):
        return self.service.clean_queue()
    
    def remote_interrupt_engine(self):
        return self.service.interrupt_engine()
    

components.registerAdapter(PerspectiveEngineFromService,
                           engineservice.EngineService,
                           IPerspectiveEngine)
