 # -*- test-case-name: ipython1.test.test_engineservice -*-

"""A Twisted Service Representation of the IPython Core.

TODO:

- Nothing for now
"""

#*****************************************************************************
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************
import cPickle as pickle
from new import instancemethod

from twisted.application import service
from twisted.internet import defer, reactor
from twisted.python import log, failure
import zope.interface as zi

from ipython1.core.shell import InteractiveShell
from ipython1.kernel import serialized, error
from ipython1.kernel.util import gatherBoth, curry

# Here is the interface specification for the IPythonCoreService

class IEngineBase(zi.Interface):
    """The Interface for the IPython Engine.
    
    All these methods should return deferreds.
    """
    id = zi.interface.Attribute("the id of the Engine object")
    
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
    

class IEngineSerialized(zi.Interface):
    
    def pushSerialized(**namespace):
        """Push a dict of keys and Serialized|objects to the user's namespace."""
    
    def pullSerialized(*keys):
        """Pull objects by key form the user's namespace as Serialized.
        
        Returns a list or one of Serialized.
        """
    

class IEngineThreaded(zi.Interface):
    pass

class IEngineQueued(zi.Interface):
    """add some queue methods to IEngine interface"""
    
    def clearQueue():
        """clear the queue"""
    

class IEngineComplete(IEngineBase, IEngineSerialized, IEngineQueued, IEngineThreaded):
    pass

def completeEngine(engine):
    """Completes an engine object"""
    zi.alsoProvides(engine, IEngineComplete)
    
    def _notImplementedMethod(name, *args, **kwargs):
        return defer.fail(NotImplementedError(
            'This method %s is not implemented by this Engine' %name))
    
    for method in IEngineComplete:
        if getattr(engine, method, 'NotDefined') == 'NotDefined':
            #if not implemented, add filler
            #could establish self.notImplemented registry here
            if callable(IEngineComplete[method]):
                setattr(engine, method, curry(_notImplementedMethod, method))
            else: 
                setattr(engine, method, None)
    assert(IEngineComplete.providedBy(engine))
    return engine

    
# Now the actual EngineService
class EngineService(service.Service):
    """Wrap IPython into a IEngineFoo implementing Twisted Service."""
    
    zi.implements(IEngineBase, IEngineSerialized)
    
    id = None
    
    def __init__(self, mpi=None):
        self.shell = InteractiveShell()
        self.mpi = mpi
        if self.mpi is not None:
            log.msg("MPI started with rank = %i and size = %i" % 
                (self.mpi.rank, self.mpi.size))
            self.id = self.mpi.rank
    
    def startService(self):
        self.shell.update({'mpi': self.mpi})
            
    # The IEngine methods
    
    def execute(self, lines):
        d = defer.execute(self.shell.execute, lines)
        d.addCallback(self.addIDToResult)
        return d
        
    def addIDToResult(self, result):
        return (self.id,) + result

    def push(self, **namespace):
        return defer.execute(self.shell.update, namespace)
    
    def pushSerialized(self, **sNamespace):
        ns = {}
        for k,v in sNamespace.iteritems():
            if isinstance(v, serialized.Serialized):
                try:
                    ns[k] = v.unpack()
                except pickle.PickleError:
                    return defer.fail()
            else:
                ns[k] = v
        return defer.execute(self.shell.update, ns)
    
    def pull(self, *keys):
        if len(keys) > 1:
            pulledDeferreds = []
            for key in keys:
                pulledDeferreds.append(defer.execute(self.shell.get,key))
            d = gatherBoth(pulledDeferreds)
            return d
        else:
            return defer.execute(self.shell.get, keys[0])
    
    def pullSerialized(self, *keys):
        if len(keys) > 1:
            pulledDeferreds = []
            for key in keys:
                d = defer.execute(self.shell.get,key)
                d.addCallback(serialized.serialize, key)
                d.addErrback(self.handlePullProblems)
                pulledDeferreds.append(d)
            dList = gatherBoth(pulledDeferreds)               
            return dList
        else:
            key = keys[0]
            d = defer.execute(self.shell.get, key)
            d.addCallback(serialized.serialize, key)
            d.addErrback(self.handlePullProblems)
            return d
            
    def handlePullProblems(self, reason):
        # reason.printTraceback()
        return serialized.serialize(reason, 'FAILURE')
            
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
        d = defer.execute(self.shell.getCommand, i)
        d.addCallback(self.addIDToResult)
        return d
    
    def status(self):
        remotes = {}
        for k,v in self.shell.locals.iteritems():
            if k not in ['__name__', '__doc__', '__console__', '__builtins__']:
                remotes[k] = v
        # print remotes
        return defer.succeed(remotes)
    

# Now the implementation of the QueuedEngine

class QueuedEngine(object):
    """a Queued wrapper for any IEngine object"""
    zi.implements(IEngineQueued)
    
    def __init__(self, engine, saveLocals=False):
        """@arg saveLocals:
            whether to update the remote status when the queue is empty.  defaults
            to False."""
        self.engine = engine
        self.id = engine.id
        self.queued = []
        self.history = {}
        self.locals = {}
        self.upToDate = True
        self.saveLocals = saveLocals
        self.currentCommand = None
        self.registerMethods()
    
    def registerMethods(self):
        zi.alsoProvides(self, *self.engine.__provides__)
        for m in dir(self.engine):
            if m in IEngineComplete and callable(IEngineComplete[m])\
                    and not getattr(self, m, None):
                # if m is a method of IEngine, and not already specified
                f = self.buildQueuedMethod(m)
                setattr(self, m, instancemethod(f, self, self.__class__))
    
    def buildQueuedMethod(self, m):
        args = IEngineComplete[m].getSignatureString()[1:-1]#strip '()'
#        log.msg("autoqueue method %s" %m)
        if args:
            comma = ', '
        else:
            comma = ''
        defs = """
def queuedMethod(self%s%s):
    return self.submitCommand(Command('%s', %s))
""" % (comma, args, m, args)
        exec(defs)
        return queuedMethod
    
    #methods from IEngineQueued:
    def clearQueue(self):
        """clear the queue"""
        for cmd in self.queued:
            cmd.deferred.errback(failure.Failure(error.QueueCleared()))
        self.queued = []
        return defer.succeed(True)
    
    #queue methods:
    def submitCommand(self, cmd):
        """submit command to queue"""
        d = defer.Deferred()
        cmd.setDeferred(d)
        self.upToDate = not self.saveLocals
        if self.currentCommand is not None:
            #log.msg("Queueing: " + repr(cmd))
            self.queued.append(cmd)
            return d
        self.currentCommand = cmd
        self.runCurrentCommand()
        return d
    
    def runCurrentCommand(self):
        """run current command"""
        cmd = self.currentCommand
        #log.msg("Starting: " + repr(self.currentCommand))
        f = getattr(self.engine, cmd.remoteMethod, None)
        if f:
            d = f(*cmd.args, **cmd.kwargs)
            if cmd.remoteMethod is 'execute':
                d.addCallback(self.saveResult)
            d.addCallback(self.finishCommand)
            d.addErrback(self.abortCommand)
        else:
            return defer.fail(AttributeError(cmd.remoteMethod))
    
    def _flushQueue(self):
        """pop next command in queue, run it"""
        if len(self.queued) > 0:
            self.currentCommand = self.queued.pop(0)
            self.runCurrentCommand()
        elif not self.upToDate:
            d = self.submitCommand(Command('status'))
            self.upToDate = True
            return d.addCallback(self.updateStatus)
    
    def saveResult(self, result):
        """put the result in the history"""
        self.history[result[1]] = result
        return result
    
    def finishCommand(self, result):
        """finish currrent command"""
        #log.msg("Finishing: " + repr(self.currentCommand) + ':' + repr(result))
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
        return None
        #return reason
    def updateStatus(self, locals):
        self.locals = locals
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
        dikt = {'queue':map(repr,self.queued), 'history':self.history}
        if self.saveLocals:
            dikt['locals'] = self.locals
        return defer.succeed(dikt)
    
    def getResult(self, i=None):
        """Get the stdin/stdout/stderr of command i."""
        if i is None:
            i = max(self.history.keys()+[None])

        cmd = self.history.get(i, None)
        if cmd is None:
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
        if not self.args:
            args = ''
        else:
            args = str(self.args)[1:-1]
        for k,v in self.kwargs.iteritems():
            if args:
                args += ', '
            args += '%s=%r' %(k,v)
        return "%s(%s)" %(self.remoteMethod, args)
    
    def handleResult(self, result):
        """When the result is ready, relay it to self.deferred."""
        self.deferred.callback(result)
    
    def handleError(self, reason):
        """When an error has occured, relay it to self.deferred."""
        # log.msg("Traceback from remote host: " + reason.getErrorMessage())
        self.deferred.errback(reason)
    

