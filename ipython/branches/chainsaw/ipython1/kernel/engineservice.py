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
    def getID(self):
        """return this.id"""
    
    def setID(self, id):
        """set this.id"""
    
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
    
    def kill(self):
        """kill the process"""
    
    def getCommand(self, i=None):
        """Get the stdin/stdout/stderr of command i."""
    
    def getLastCommandIndex(self):
        """Get the index of the last command."""
    

class IQueuedEngine(IEngine):
    """add some queue methods to IEngine interface"""
    
    def clearQueue(self):
        """clear the queue"""
    
    def status(self):
        """return queue and history"""
    

class QueuedEngine(object):
    
    implements(IQueuedEngine)
    
    def __init__(self, engine):
        self.engine = engine
        self.id = engine.id
        self.queued = []
        self.history = {}
        self.currentCommand = None
    
    #methods from IQueuedEngine:
    def clearQueue(self):
        """clear the queue"""
        self.queued = []
    
    def status(self):
        return {'queue':self.queued, 'history':self.history}
    
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
            d = f(*cmd.args)
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
    
    def getID(self):
        return self.id
    
    def setID(self, id):
        self.id = id
        return self.submitCommand(Command("setID", id))
    
    def execute(self, lines):
        """Execute lines of Python code."""
        return self.submitCommand(Command("execute", lines))
    
    def put(self, key, value):
        """Put value into locals namespace with name key."""
        d = self.submitCommand(Command("put", key, value))
        return d
    
    def putPickle(self, key, package):
        """Unpickle package and put into the locals namespace with name key."""
        d = self.submitCommand(Command("putPickle", key, package))
        return d
    
    def get(self, key):
        """Gets an item out of the self.locals dict by key."""
        d = self.submitCommand(Command("get", key))
        return d
    
    def getPickle(self, key):
        """Gets an item out of the self.locals dist by key and pickles it."""
        d = self.submitCommand(Command("getPickle", key))
        return d
    
    def update(self, dictOfData):
        """Gets an item out of the self.locals dict by key."""
        d = self.submitCommand(Command("update", dictOfData))
        return d
    
    def updatePickle(self, dictPickle):
        """Gets an item out of the self.locals dist by key and pickles it."""
        d = self.submitCommand(Command("updatePickle", dictPickle))
        return d
    
    def reset(self):
        """Reset the InteractiveShell."""
        d = self.submitCommand(Command("reset"))
        return d
    
    def kill(self):
        """kill the InteractiveShell."""
        self.clearQueue()
        d = self.submitCommand(Command("kill"))
        return d
    
    def getCommand(self, i=None):
        """Get the stdin/stdout/stderr of command i."""
        try:
            return defer.succeed(self.history[i])
        except KeyError:
            return defer.succeed(None)
    
    def getLastCommandIndex(self):
        """Get the index of the last command."""
#        d = self.submitCommand(Command("getLastCommandIndex"))
        return defer.succeed(max(self.history.keys()+[-1]))
    

#Command object for queued Engines
class Command(object):
    """A command that will be sent to the Remote Engine."""
    
    def __init__(self, remoteMethod, *args):
        """Build a new Command object."""
        
        self.remoteMethod = remoteMethod
        self.args = args
    
    def setDeferred(self, d):
        """Sets the deferred attribute of the Command."""    
        self.deferred = d
    
    def __repr__(self):
        return "Command: " + self.remoteMethod + repr(self.args)
    
    def handleResult(self, result):
        """When the result is ready, relay it to self.deferred."""
        self.deferred.callback(result)
    
    def handleError(self, reason):
        """When an error has occured, relay it to self.deferred."""
        log.msg("Traceback from remote host: " + reason.getErrorMessage())
        self.deferred.errback(reason)
    

# Now the actual EngineService
class EngineService(InteractiveShell, service.Service):
    
    implements(IEngine)
    
    id = None
    
    def getID(self):
        return self.id
    
    def setID(self, id):
        self.id = id
    
    def put(self, key, value):
        return defer.succeed(InteractiveShell.put(self, key, value))
    
    def putPickle(self, key, package):
        value = pickle.loads(package)
        return self.put(key, value)
    
    def get(self, key):
        return defer.succeed(InteractiveShell.get(self, key))
    
    def getPickle(self, key):
        value = self.get(key)
        value.addCallback(lambda v: pickle.dumps(v, 2))
        return value
    
    def update(self, dictOfData):
        return defer.succeed(InteractiveShell.update(self, dictOfData))
    
    def updatePickle(self, dictPickle):
        value = pickle.loads(dictPickle)
        return self.update(value)
    
    def reset(self):
        return defer.succeed(InteractiveShell.reset(self))
    
    def kill(self):
        try:
            reactor.stop()
        except RuntimeError:
            log.msg("Can't stop reactor, probably already stopped")
    
    def getCommand(self, i=None):
        return defer.succeed(InteractiveShell.getCommand(self, i))
    
    def getLastCommandIndex(self):
        return defer.succeed(InteractiveShell.getLastCommandIndex(self))
    
    