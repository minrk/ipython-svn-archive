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
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import os, signal, time

from twisted.application import service, internet
from twisted.internet import defer, reactor
from twisted.python import log
from zope.interface import Interface, implements

import cPickle as pickle

from ipython1.core.shell import InteractiveShell

# Here is the interface specification for the IPythonCoreService

class IEngine(Interface):
    """The Interface for the IPython Engine.
    
    For now, the methods in this interface must not return deferreds.  This is
    because the EngineService will be adapted to different protocols, each of
    which need to handle errors in different ways.  Thus, when esceptions are
    raised in these methods, they must be allowed to propagate.  That is, they
    must not be caught.
    """
    
    def execute(self, lines):
        """Execute lines of Python code."""
    
    def put(self, key, value):
        """Put value into locals namespace with name key."""
    
    def putPickle(self, key, package):
        """Unpickle package and put into the locals namespace with name key."""
    
    def get(self, key):
        """Gets an item out of the self.locals dict by key."""
    
    def getPickle(self, key):
        """Gets an item out of the self.locals dist by key and pickles it."""
    
    def update(self, dictOfData):
        """Updates the self.locals dict with the dictOfData."""
    
    def updatePickle(self, dictPickle):
        """Updates the self.locals dict with the pickled dict."""
    
    def reset(self):
        """Reset the InteractiveShell."""
    
    def getCommand(self, i=None):
        """Get the stdin/stdout/stderr of command i."""
    
    def getLastCommandIndex(self):
        """Get the index of the last command."""
    

# Now the actual EngineService implementation                   
class EngineService(InteractiveShell, service.Service):
    
    implements(IEngine)
    
    def __init__(self, locals=None,
                    filename="<console>", restart=False):
                    
        InteractiveShell.__init__(self, locals, filename)
        self.restart = restart
    
    def putPickle(self, key, package):
        value = pickle.loads(package)
        return self.put(key, value)
    
    def getPickle(self, key):
        value = self.get(key)
        package = pickle.dumps(value, 2)
        return package
    
    def updatePickle(self, dictPickle):
        value = pickle.loads(dictPickle)
        return self.update(value)
    
