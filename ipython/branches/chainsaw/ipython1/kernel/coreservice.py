"""A Twisted Service Representation of the IPython Core

TODO:

- Make it possible to interupt the kernel engine to stop the current
  command/
- Use pb.Error subclasses to pass exceptions back to the calling process.
  For this I can put calls to ishell in a try/except clause:
  
    try:
        result = self.ishell.execute(lines)
    except Exception:
        raise pb.Error("execute()")
    else:
        return defer.succeed(self.ishell.execute(lines))  

  The argument of the pr.Error is then available on the other side as
  getErrorMessage().  
- Security issues.  Turn on TLS an authentication.
"""

import os, signal

from twisted.application import internet, service
from twisted.internet import protocol, reactor, defer
from twisted.python import components, log
from twisted.web import xmlrpc
from zope.interface import Interface, implements
from twisted.spread import pb

import cPickle as pickle

from ipython1.core.shell import InteractiveShell

# Here is the interface specification for the IPythonCoreService

class ICoreService(Interface):
    """The Interface for the IPython Core"""
    
    def execute(self, lines):
        """Execute lines of Python code."""
    
    def put(self, key, value):
        """Put value into locals namespace with name key."""
        
    def put_pickle(self, key, package):
        """Unpickle package and put into the locals namespace with name key."""
        
    def get(self, key):
        """Gets an item out of the self.locals dict by key."""

    def get_pickle(self, key):
        """Gets an item out of the self.locals dist by key and pickles it."""

    def reset(self):
        """Reset the InteractiveShell."""
        
    def get_command(self, i=None):
        """Get the stdin/stdout/stderr of command i."""

    def get_last_command_index(self):
        """Get the index of the last command."""

# Now the actual CoreService implementation                   

class CoreService(service.Service):

    implements(ICoreService)
    
    def __init__(self, ):
        self.ishell = InteractiveShell()
                
    def execute(self, lines):
        return defer.succeed(self.ishell.execute(lines))
    
    def put(self, key, value):
        return defer.succeed(self.ishell.put(key, value))
        
    def put_pickle(self, key, package):
        try:
            value = pickle.loads(package)
        except pickle.PickleError:
            return defer.fail()  # probably should raise pb.Error("msg")
        else:
            return defer.succeed(self.ishell.put(key, value))
        
    def get(self, key):
        return defer.succeed(self.ishell.get(key))

    def get_pickle(self, key):
        value = self.ishell.get(key)
        try:
            package = pickle.dumps(value, 2)
        except pickle.PickleError:
            return defer.fail()  # probably should raise pb.Error("msg")
        else:
            return defer.succeed(package)

    def reset(self):
        return defer.succeed(self.ishell.reset())
        
    def get_command(self, i=None):
        return defer.succeed(self.ishell.get_command(i))

    def get_last_command_index(self):
        return defer.succeed(self.ishell.get_last_command_index())
     
# Expose a PB interface to the CoreService
     
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
    
components.registerAdapter(PerspectiveCoreFromService,
                           CoreService,
                           IPerspectiveCore)