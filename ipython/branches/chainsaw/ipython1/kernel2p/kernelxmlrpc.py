"""Expose the IPython Kernel Service using XML-RPC.

This module specifies the IPerspectiveKenel Interface and its implementation
as an Adapter from the IKernelService Interface.  This adapter wraps
KernelService instance into something that inherits from pd.Root.  This makes
is callable using Perspective Broker.

Any public methods of the IKernelService Interface that should be available over
PB must be added to both the Interface and Adapter in this file.

This module must be imported in its entirety to have its Adapters registered
properly:

from ipython1.kernel import kernelpb
"""


from twisted.python import components
from twisted.web import xmlrpc
from zope.interface import Interface, implements

from ipython1.kernel2p import kernelservice

# Expose a PB interface to the KernelService
     
class IXMLRPCKernel(Interface):

    def xmlrpc_execute(self, lines):
        """Execute lines of Python code."""
    
    def xmlrpc_put(self, key, value):
        """Put value into locals namespace with name key."""
        
    def xmlrpc_put_pickle(self, key, package):
        """Unpickle package and put into the locals namespace with name key."""
        
    def xmlrpc_get(self, key):
        """Gets an item out of the self.locals dict by key."""

    def xmlrpc_get_pickle(self, key):
        """Gets an item out of the self.locals dist by key and pickles it."""

    def xmlrpc_reset(self):
        """Reset the InteractiveShell."""
        
    def xmlrpc_get_command(self, i=None):
        """Get the stdin/stdout/stderr of command i."""

    def xmlrpc_get_last_command_index(self):
        """Get the index of the last command."""

    def xmlrpc_restart_engine(self):
        """Stops and restarts the kernel engine process."""
        
    def xmlrpc_clean_queue(self):
        """Cleans out pending commands in the kernel's queue."""
        
    def xmlrpc_interrupt_engine(self):
        """Send SIGUSR1 to the kernel engine to stop the current command."""

class XMLRPCKernelFromService(xmlrpc.XMLRPC):

    implements(IXMLRPCKernel)

    def __init__(self, service):
        self.service = service

    def xmlrpc_execute(self, lines):
        return self.service.execute(lines)
    
    def xmlrpc_put(self, key, value):
        return self.service.put(key, value)
        
    def xmlrpc_put_pickle(self, key, package):
        return self.service.put_pickle(key, package)
        
    def xmlrpc_get(self, key):
        return self.service.get(key)

    def xmlrpc_get_pickle(self, key):
        return self.service.get_pickle(key)

    def xmlrpc_reset(self):
        return self.service.reset()
        
    def xmlrpc_get_command(self, i=None):
        return self.service.get_command(i)

    def xmlrpc_get_last_command_index(self):
        return self.service.get_last_command_index()

    def xmlrpc_restart_engine(self):
        return self.service.restart_engine()
        
    def xmlrpc_clean_queue(self):
        return self.service.clean_queue()

    def xmlrpc_interrupt_engine(self):
        return self.service.interrupt_engine()
    
components.registerAdapter(XMLRPCKernelFromService,
                           kernelservice.KernelService,
                           IXMLRPCKernel)
    
    
    
