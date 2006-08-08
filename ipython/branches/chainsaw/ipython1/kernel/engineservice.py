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

- Generate the IEngine interface as a set of disjoint mixins
- Create a basic NotImplementedEngine
- Make our engine inherit from that
- 

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
from twisted.python import log, failure
from zope.interface import Interface, implements, interface
#from zope.interface.interface import Attribute

from ipython1.core.shell import InteractiveShell

# Here is the interface specification for the IPythonCoreService

class IEngineBase(Interface):
    """The Interface for the IPython Engine.
    
    All these methods should return deferreds.
    """
    id = interface.Attribute("the id of the Engine object")
    
    def execute(lines):
        """Execute lines of Python code.
        
        Returns deferred to tuple of (id, stdin, stdout, stderr)
        """
    
    def push(**namespace):
        """Push dict namespace into the user's namespace.
        
        Returns deferred to None
        """

    def pull(*keys):
        """Pulls values out of the user's namespace by keys.
        
        Returns deferred to tuple or object
        """
    
    def pullNamespace(*keys):
        """Pulls values by key from user's namespace as dict."""
    
    def getResult(i=None):
        """Get the stdin/stdout/stderr of command i."""
    
    def reset():
        """Reset the InteractiveShell."""
    
    def kill():
        """kill the process"""
    
    def status():
        """return status of engine"""
    
class IRemoteEngine(Interface):
    
    def pushSerialized(**namespace):
        """Push a dict of keys and Serialized to the user's namespace."""
        
    def pullSerialized(*keys):
        """Pull objects by key form the user's namespace as Serialized."""
    
class IThreadedEngine(Interface):
    pass
    
class IQueuedEngine(Interface):
    """add some queue methods to IEngine interface"""

    def clearQueue():
        """clear the queue"""

class IEngine(IEngineBase, IRemoteEngine, IQueuedEngine, IThreadedEngine):
    pass

class NotImplementedEngine(object):
    
    implements(IEngine)

    id = None

    # IEngineBase
    def execute(self, lines):
        defer.fail(NotImplementedError('This method is not implemented by this Engine'))
        
    def push(self, **namespace):
        defer.fail(NotImplementedError('This method is not implemented by this Engine'))
        
    def pull(self, *keys):
        defer.fail(NotImplementedError('This method is not implemented by this Engine'))
    
    def pullNamespace(self, *keys):
        defer.fail(NotImplementedError('This method is not implemented by this Engine'))
    
    def getResult(self, i=None):
        defer.fail(NotImplementedError('This method is not implemented by this Engine'))
    
    def reset(self):
        defer.fail(NotImplementedError('This method is not implemented by this Engine'))
    
    def kill(self):
        defer.fail(NotImplementedError('This method is not implemented by this Engine'))
    
    def status(self):
        defer.fail(NotImplementedError('This method is not implemented by this Engine'))

    # IRemoteEngine
    def pushSerialized(self, **namespace):
        defer.fail(NotImplementedError('This method is not implemented by this Engine'))
        
    def pullSerialized(self, *keys):
        defer.fail(NotImplementedError('This method is not implemented by this Engine'))

    # IQueuedEngine        
    def clearQueue(self):
        defer.fail(NotImplementedError('This method is not implemented by this Engine'))

# Now the actual EngineService
class EngineService(service.Service, NotImplementedEngine):
    
    implements(IEngine)
    
    id = None
    
    def __init__(self):
        self.shell = InteractiveShell()# let's use containment, not inheritance
    
    # The IEngine methods
    
    def execute(self, lines):
        return defer.execute(self.shell.execute, lines)
    
    def push(self, **namespace):
        return defer.execute(self.shell.update, namespace)
    
    def pull(self, *keys):
        if len(keys) > 1:
            result = []
            for key in keys:
                result.append(self.shell.get(key))
            return defer.succeed(tuple(result))
        else:
            return defer.execute(self.shell.get, keys[0])
    
    def pullNamespace(self, *keys):
        ns = {}
        for key in keys:
            ns[key] = self.shell.get(key)
        return defer.succeed(ns)
    
    def reset(self):
        return defer.execute(self.shell.reset)
    
    def kill(self):
        try:
            reactor.stop()
        except RuntimeError:
            log.msg('The reactor was not running apparently.')
            return defer.fail()
        else:
            return defer.succeed(None)
    
    def getResult(self, i=None):
        return defer.execute(self.shell.getCommand, i)
    
    def status(self):
        return defer.succeed(None)

# Now the implementation of the QueuedEngine

class QueuedEngine(object):
    
    implements(IEngine)
    
    def __init__(self, engine):
        self.engine = engine
        self.queued = []
        self.history = {}
        self.currentCommand = None
        self.registerMethods()

    #methods from IQueuedEngine:
    def clearQueue(self):
        """clear the queue"""
        self.queued = []
    
    #queue methods:
    def submitCommand(self, cmd):
        """submit command to queue"""
        d = defer.Deferred()
        cmd.setDeferred(d)
        if self.currentCommand is not None:
            log.msg("Queueing: " + repr(cmd))
            self.queued.append(cmd)
            return d
        self.currentCommand = cmd
        self.runCurrentCommand()
        return d
    
    def runCurrentCommand(self):
        """run current command"""
        cmd = self.currentCommand
        log.msg("Starting: " + repr(self.currentCommand))
        f = getattr(self.engine, cmd.remoteMethod, None)
        if f:
            d = f(*cmd.args, **cmd.kwargs)
            if cmd.remoteMethod is 'execute':
                d.addCallback(self.saveResult)
            d.addCallback(self.finishCommand)
            d.addErrback(self.abortCommand)
        else:
            raise 'no such method'
    
    def _flushQueue(self):
        """pop next command in queue, run it"""
        if len(self.queued) > 0:
            self.currentCommand = self.queued.pop(0)
            self.runCurrentCommand()
    
    def saveResult(self, result):
        """put the result in the history"""
        self.history[result[0]] = result
        return result
    
    def finishCommand(self, result):
        """finish currrent command"""
        log.msg("Finishing: " + repr(self.currentCommand) + ':' + repr(result))
        self.currentCommand.handleResult(result)
        del self.currentCommand
        self.currentCommand = None
        self._flushQueue()
        return result
    
    def abortCommand(self, reason):
        """abort current command"""
        self.currentCommand.handleError(reason)
        del self.currentCommand
        self.currentCommand = None
        self._flushQueue()
        #return reason
    
    def registerMethods(self):
        for m in dir(self.engine):
            if m in IEngine and isinstance(IEngine[m], interface.Method)\
                and not getattr(self, m, None):
                # if m is a method of IEngine, and not already specified
                    f = self.buildQueuedMethod(m)
                    setattr(self, m, f)
    
    def buildQueuedMethod(self, m):
        def f(*args, **kwargs):
            return self.submitCommand(Command(m, *args, **kwargs))
        return f
    
    #methods from IEngine
    def reset(self):
        """Reset the InteractiveShell."""
        self.clearQueue()
        self.history = {}  # reset the cache - I am not sure we should do this
        return self.submitCommand(Command("reset"))
    
    def kill(self):
        """kill the InteractiveShell."""
        self.clearQueue()
        return self.submitCommand(Command("kill"))
    
    def status(self):
        """Get the status {queue, history} of the engine"""
        return defer.succeed({'queue':self.queued, 'history':self.history})
    
    def getResult(self, i=None):
        """Get the stdin/stdout/stderr of command i."""
        if i is None:
            i = max(self.history.keys()+[None])
        try:
            cmd = self.history[i]
        except KeyError:
            return self.submitCommand(Command("getResult", i))
        else:
            return defer.succeed(cmd)

#Command object for queued Engines
class Command(object):
    """A command that will be sent to the Remote Engine."""
    
    def __init__(self, remoteMethod, *args, **kwargs):
        """Build a new Command object."""
        
        self.remoteMethod = remoteMethod
        self.args = args
        self.kwargs = kwargs
    
    def setDeferred(self, d):
        """Sets the deferred attribute of the Command."""    
        self.deferred = d
    
    def __repr__(self):
        return "Command: " + self.remoteMethod + repr(self.args) + repr(self.kwargs)
    
    def handleResult(self, result):
        """When the result is ready, relay it to self.deferred."""
        self.deferred.callback(result)
    
    def handleError(self, reason):
        """When an error has occured, relay it to self.deferred."""
        log.msg("Traceback from remote host: " + reason.getErrorMessage())
        self.deferred.errback(reason)
    

