# -*- test-case-name: ipython1.test.test_coreservice -*-

"""A Twisted Service Representation of the IPython Core.

This file contains the ICoreService Interface specification.  Any public 
methods in ipython core must be given here.  If they are not meant to be public
they should not appear here.

The CoreService should not make any assumptions about what network protocols 
will be used to expose it.  The Interfaces and Adapters used for this purpose
can be found in the files corepb.py, corehttp.py, etc.

TODO:

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

from twisted.application import service
from twisted.internet import defer
from twisted.python import log
from zope.interface import Interface, implements

import cPickle as pickle

from ipython1.core.shell import InteractiveShell

# Here is the interface specification for the IPythonCoreService

class ICoreService(Interface):
    """The Interface for the IPython Core.
    
    For now, the methods in this interface must not return deferreds.  This is
    because the CoreService will be adapted to different protocols, each of
    which need to handle errors in different ways.  Thus, when esceptions are
    raised in these methods, they must be allowed to propagate.  That is, they
    must not be caught.
    """
    
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

    def update(self, dict_of_data):
        """Updates the self.locals dict with the dict_of_data."""
        
    def update_pickle(self, dict_pickle):
        """Updates the self.locals dict with the pickled dict."""
        
    def reset(self):
        """Reset the InteractiveShell."""
        
    def get_command(self, i=None):
        """Get the stdin/stdout/stderr of command i."""

    def get_last_command_index(self):
        """Get the index of the last command."""

# Now the actual CoreService implementation                   

class CoreService(InteractiveShell, service.Service):

    implements(ICoreService)
    
    def put_pickle(self, key, package):
        value = pickle.loads(package)
        return self.put(key, value)
        
    def get_pickle(self, key):
        value = self.get(key)
        package = pickle.dumps(value, 2)
        return package
        
    def update_pickle(self, dict_pickle):
        value = pickle.loads(package)
        return self.update(value)    