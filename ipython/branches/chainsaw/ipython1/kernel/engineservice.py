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
from twisted.python import log, failure
from zope.interface import Interface, implements
from zope.interface.interface import Attribute

import cPickle as pickle

from ipython1.core.shell import InteractiveShell

# Here is the interface specification for the IPythonCoreService

class IEngine(Interface):
    """The Interface for the IPython Engine.
    
    All these methods should return deferreds.
    """
    id = Attribute("the id of the Engine object")
    
    def execute(lines):
        """Execute lines of Python code."""
    
    def push(key, value):
        """Put value into locals namespace with name key."""

    def pushNamespace(namespace):
        """"""

    def pull(keys):
        """Gets an item out of the self.locals dict by key."""
    
    def pullNamespace(namespace):
        """"""
    
    def getResult(i=None):
        """Get the stdin/stdout/stderr of command i."""
    
    def reset():
        """Reset the InteractiveShell."""
    
    def kill():
        """kill the process"""
    
    def status():
        """return status of engine"""
    

# Now the actual EngineService
class EngineService(service.Service):
    
    implements(IEngine)
    
    id = None
    def __init__(self):
        self.shell = InteractiveShell()# let's use containment, not inheritance
    
    # The IEngine methods
    
    def execute(self, lines):
        return defer.execute(self.shell.execute, lines)
    
    def push(self, **namespace):
        return defer.execute(self.shell.update, namespace)
    
    def pushPickle(self, pickledNamespace):
        return self.push(**pickle.loads(pickledNamespace))
    
    def pull(self, *keys):
        result = []
        for key in keys:
            result.append(self.shell.get(key))
        return defer.succeed(tuple(result))
    
    def pullPickle(self, *keys):
        return self.pull(*keys).addCallback(lambda v: pickle.dumps(v,2))
    
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
        return defer.execute(self.shell.getResult, i)
    
    def getLastCommandIndex(self):
        return defer.execute(self.shell.getLastCommandIndex)
    
    def status(self):
        return defer.succeed(None)

# Now the interface and implementation of the QueuedEngine

class IQueuedEngine(IEngine):
    """add some queue methods to IEngine interface"""
    
    def clearQueue():
        """clear the queue"""
    

class QueuedEngine(object):
    
    implements(IQueuedEngine)
    
    def __init__(self, engine):
        self.engine = engine
        
        self.queued = []
        self.history = {}
        self.currentCommand = None
    
    
    
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
    
    #methods from IEngine
    
    def execute(self, lines):
        """Execute lines of Python code."""
        return self.submitCommand(Command("execute", lines))
    
    def push(self, **namespace):
        """Put value into locals namespace with name key."""
        return self.submitCommand(Command("push", **namespace))

    def pushPickle(self, pickleNamespace):
        """Unpickle package and put into the locals namespace with name key."""
        return self.submitCommand(Command("pushPickle", pickleNamespace))
    
    def pull(self, *keys):
        """Gets an item out of the self.locals dict by key."""
        return self.submitCommand(Command("pull", *keys))
    
    def pullPickle(self, *keys):
        """Gets an item out of the self.locals dist by key and pickles it."""
        return self.submitCommand(Command("pullPickle", *keys))
    
    def reset(self):
        """Reset the InteractiveShell."""
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
            d = self.getLastCommandIndex()
            d.addCallback(lambda i: self.history[i])
            return d
        else:
            try:
                cmd = self.history[i]
            except KeyError:
                return defer.fail()
            else:
                return defer.succeed(cmd)
    
    def getLastCommandIndex(self):
        """Get the index of the last command."""
        return defer.succeed(max(self.history.keys()+[-1]))
    

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
    

