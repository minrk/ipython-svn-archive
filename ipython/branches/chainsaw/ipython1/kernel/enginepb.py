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
    """Twisted Perspective Broker remote interface for engine service."""
    
    #get/set methods for state variables
    def remote_get_state(self):
        """get restart, saveID"""
    
    def remote_set_state(self, r, s):
        """set restart, saveID"""
        
    #remote methods for engine service
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
        
    def remote_interrupt_engine(self):
        """Send SIGUSR1 to the kernel engine to stop the current command."""
    

class PerspectiveEngine(pb.Referenceable):
    
    implements(IPerspectiveEngine)
    
    def __init__(self, service):
        self.service = service
        self.service.connection = self
        self.d = self.service.factory.getRootObject()
        self.d.addCallbacks(self._connect, self._failure)
    
    def _connect(self, obj):
        """callback for pb.PBClientFactory.getRootObject"""
        self.root = obj
        if self.service.restart:
            d = self.root.callRemote('reconnectEngine', self.service.id, self)
            d.addErrback(self._failure2)
        else:
            d = self.root.callRemote('registerEngine', self)
            d.addCallbacks(self._connected, self._failure)
        return d
    
    def _failure(self, reason):
        """callback for pb.PBClientFactory.getRootObject"""
        raise Exception(reason)
    
    def _failure2(self, reason):
        """callback for pb.PBClientFactory.getRootObject"""
        raise Exception(reason)
    
    def _connected(self, arg):
        """arg = (id, restart, saveID)"""
        self.service.id = arg[0]
        self.service.restart = arg[1]
        self.service.saveID = arg[2]
        log.msg("got ID: %r" %self.service.id)
        return self.service.id
    
    def remote_get_state(self):
        return (self.service.restart, self.service.saveID)
    
    def remote_set_state(self, s):
        self.service.restart = s[0]
        self.service.saveID = s[1]
    
    def remote_get_saveID(self):
        return self.service.saveID
    
    def remote_set_saveID(self,s):
        self.service.saveID = s
    
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
    
    def remote_interrupt_engine(self):
        return self.service.interrupt_engine()
    

components.registerAdapter(PerspectiveEngine,
                           engineservice.EngineService,
                           IPerspectiveEngine)
