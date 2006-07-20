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
    def remote_getState(self):
        """get restart, saveID"""
    
    def remote_setState(self, r, s):
        """set restart, saveID"""
        
    #remote methods for engine service
    def remote_execute(self, lines):
        """Execute lines of Python code."""
    
    def remote_put(self, key, value):
        """Put value into locals namespace with name key."""
    
    def remote_putPickle(self, key, package):
        """Unpickle package and put into the locals namespace with name key."""
    
    def remote_get(self, key):
        """Gets an item out of the self.locals dict by key."""
    
    def remote_getPickle(self, key):
        """Gets an item out of the self.locals dist by key and pickles it."""
    
    def remote_reset(self):
        """Reset the InteractiveShell."""
    
    def remote_getCommand(self, i=None):
        """Get the stdin/stdout/stderr of command i."""
    
    def remote_getLastCommandIndex(self):
        """Get the index of the last command."""
    
    def remote_restartEngine(self):
        """Stops and restarts the engine service."""
        
    def remote_interruptEngine(self):
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
            d = self.root.callRemote('reconnectEngine', self.service.id, self
            ).addCallbacks(self._reconnected, self._failure)
        else:
            d = self.root.callRemote('registerEngine', self)
            d.addCallbacks(self._connected, self._failure)
        return d
    
    def _failure(self, reason):
        """errback for pb.PBClientFactory.getRootObject"""
        reason.raiseException()
    
    def _connected(self, arg):
        """arg = (id, restart)"""
        self.service.id = arg[0]
        self.service.restart = arg[1]
        log.msg("got ID: %r" %self.service.id)
        return self.service.id
    
    def _reconnected(self, _):
        log.msg("reconnected to controller")
    
    def remote_getRestart(self):
        return self.service.restart
    
    def remote_setRestart(self, r):
        self.service.restart = r
    
    def remote_getSaveID(self):
        return self.service.saveID
    
    def remote_setSaveID(self,s):
        self.service.saveID = s
    
    def remote_execute(self, lines):
        return self.service.execute(lines)
    
    def remote_put(self, key, value):
        return self.service.put(key, value)
    
    def remote_putPickle(self, key, package):
        return self.service.putPickle(key, package)
    
    def remote_get(self, key):
        return self.service.get(key)
    
    def remote_getPickle(self, key):
        return self.service.getPickle(key)
    
    def remote_reset(self):
        return self.service.reset()
    
    def remote_getCommand(self, i=None):
        return self.service.getCommand(i)
    
    def remote_getLastCommandIndex(self):
        return self.service.getLastCommandIndex()
    
    def remote_restartEngine(self):
        return self.service.restartEngine()
    
    def remote_interruptEngine(self):
        return self.service.interruptEngine()
    

components.registerAdapter(PerspectiveEngine,
                           engineservice.EngineService,
                           IPerspectiveEngine)
