# -*- test-case-name: ipython1.test.test_corepb -*-
"""Expose the IPython Core Service using Twisted's Perspective Broker.

This module specifies the IPerspectiveCore Interface and its implementation
as an Adapter from the ICoreService Interface.  This adapter wraps
CoreService instance into something that inherits from pd.Root.  This makes
is callable using Perspective Broker.

Any public methods of the ICoreService Interface that should be available over
PB must be added to both the Interface and Adapter in this file.

This module must be imported in its entirety to have its Adapters registered
properly:

from ipython1.kernel import corepb
"""

from twisted.python import components, failure
from twisted.spread import pb
from twisted.spread.pb import Error
from zope.interface import Interface, implements

from ipython1.kernel2p import coreservice
     
class MyError(pb.Error):
    pass

class IPerspectiveCore(Interface):

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

    def remote_update(self, dict_of_data):
        """Updates the self.locals dict with the dict_of_data."""
        
    def remote_update_pickle(self, dict_pickle):
        """Updates the self.locals dict with the pickled dict."""

    def remote_reset(self):
        """Reset the InteractiveShell."""
        
    def remote_get_command(self, i=None):
        """Get the stdin/stdout/stderr of command i."""

    def remote_get_last_command_index(self):
        """Get the index of the last command."""

class PerspectiveCoreFromService(pb.Root):

    implements(IPerspectiveCore)

    def __init__(self, service):
        self.service = service

    def remote_execute(self, lines):
        try:
            result = self.service.execute(lines)
        except:
            raise pb.Error("execute()")
        else:
            return result
            
    def remote_put(self, key, value):
        try:
            result = self.service.put(key, value)
        except:
            raise Error("put()")
        else:
            return result
        
    def remote_put_pickle(self, key, package):
        try:
            result = self.service.put_pickle(key, package)
        except:
            raise pb.Error("put_pickle()")
        else:
            return result
        
    def remote_get(self, key):
        try:
            result = self.service.get(key)
        except:
            raise pb.Error("get()")
        else:
            return result

    def remote_get_pickle(self, key):
        try:
            result = self.service.get_pickle(key)
        except:
            raise pb.Error("get_pickle()")
        else:
            return result

    def remote_update(self, dict_of_data):
        try:
            result = self.service.update(dict_of_data)
        except:
            raise pb.Error("update()")
        else:
            return result
        
    def remote_update_pickle(self, dict_pickle):
        try:
            result = self.service.update_pickle(dict_of_data)
        except:
            raise pb.Error("update_pickle()")
        else:
            return result

    def remote_reset(self):
        try:
            result = self.service.reset()
        except:
            raise pb.Error("reset()")
        else:
            return result
        
    def remote_get_command(self, i=None):
        try:
            result = self.service.get_command(i)
        except:
            raise pb.Error("get_command()")
        else:
            return result

    def remote_get_last_command_index(self):
        try:
            result = self.service.get_last_command_index()
        except:
            raise pb.Error("get_last_command_index()")
        else:
            return result
    
components.registerAdapter(PerspectiveCoreFromService,
                           coreservice.CoreService,
                           IPerspectiveCore)