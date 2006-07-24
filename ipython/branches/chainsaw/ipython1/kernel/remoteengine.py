"""The RemoteEngine interface and class for the controller service
    classes:
        IRemoteEngine(Interface) - the interface for remote engines
        RemoteEngine(object) - the implementation of RemoteEngine"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from twisted.internet import defer
from twisted.python import log, components
from zope.interface import implements

from ipython1.kernel import engineservice


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
#        print "Command: " + self.remoteMethod + repr(self.args)
        log.msg("Traceback from remote host: " + reason.getErrorMessage())
        self.deferred.errback(reason)
    

class IRemoteEngine(engineservice.IEngine):
    """add some methods to IEngine interface"""
    
    def callRemote(self, cmd):
        """make remote call, must be overridden by adapter"""
    
    def setRestart(self, r):
        """set restart"""
    
    def setRemoteRestart(self, r):
        """set restart on remote engine"""
    
    def handleDisconnect(self):
        """handle disconnection from remote engine"""
    
    def submitCommand(self, cmd):
        """submitCommand"""
    
    def runCurrentCommand(self):
        """runCurrentCommand"""
    
    def _flushQueue(self):
        """_flushQueue"""
    
    def finishCommand(self, result):
        """finishCommand"""
    
    def abortCommand(self, reason):
        """abortCommand"""
    

#now the actual implementation of RemoteEngine
class RemoteEngine(object):
    
    implements(IRemoteEngine)
    
    def __init__(self, service, id, remoteEngine=None, restart=False):
        self.service = service
        self.id = id
        self.restart = restart
        self.queued = []
        self.currentCommand = None
    
    #methods from IRemoteEngine:
    
    def setRestart(self, r):
        self.restart = r
        return self.setRemoteRestart(r)
    
    def setRemoteRestart(self, r):
        return self.callRemote('setRestart', r)
    
    def handleDisconnect(self):
        return self.service.disconnectEngine(self.id)
    
    #command methods:
    def submitCommand(self, cmd):
        
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
        
        cmd = self.currentCommand
        log.msg("Starting: " + repr(self.currentCommand))
        d = self.callRemote(cmd.remoteMethod, *(cmd.args))
        d.addCallback(self.finishCommand)
        d.addErrback(self.abortCommand)
    
    def _flushQueue(self):
        
        if len(self.queued) > 0:
            self.currentCommand = self.queued.pop(0)
            self.runCurrentCommand()
    
    def finishCommand(self, result):
        
        log.msg("Finishing: " + repr(self.currentCommand) + repr(result))
        self.currentCommand.handleResult(result)
        del self.currentCommand
        self.currentCommand = None
        self._flushQueue()
        return result
    
    def abortCommand(self, reason):
        
        self.currentCommand.handleError(reason)
        del self.currentCommand
        self.currentCommand = None
        self._flushQueue()
        #return reason
    
    #methods from IEngine
    
    def execute(self, lines):
        """Execute lines of Python code."""
        
        d = self.submitCommand(Command("execute", lines))
        return d
    
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
    
    def reset(self):
        """Reset the InteractiveShell."""
        
        d = self.submitCommand(Command("reset"))
        return d
    
    def getCommand(self, i=None):
        """Get the stdin/stdout/stderr of command i."""
        
        d = self.submitCommand(Command("getCommand", i))
        return d
    
    def getLastCommandIndex(self):
        """Get the index of the last command."""
        
        d = self.submitCommand(Command("getLastCommandIndex"))
        return d
    
