 # -*- test-case-name: ipython1.test.test_engineservice -*-
"""A Twisted Service Representation of the IPython core.

The IPython Core exposed to the network is called the Engine.  Its
representation in Twisted in the EngineService.  Interfaces and adapters
are used to abstract out the details of the actual network protocol used.
The EngineService is an Engine that knows nothing about the actual protocol
used.

The EngineService is exposed with various network protocols in modules like:

enginepb.py
enginevanilla.py
"""
__docformat__ = "restructuredtext en"
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import cPickle as pickle
from new import instancemethod

from twisted.application import service
from twisted.internet import defer, reactor
from twisted.python import log, failure
import zope.interface as zi

from ipython1.kernel import serialized, error, util
from ipython1.kernel.util import gatherBoth, curry


#-------------------------------------------------------------------------------
# Interface specification for the Engine
#-------------------------------------------------------------------------------

class IEngineBase(zi.Interface):
    """The Interface for the IPython Engine.
    
    This interface provides a formal specification of the IPython core.
    All these methods should return deferreds regardless of what side of a
    network connection they are on.
    """
    
    id = zi.interface.Attribute("the id of the Engine object")
    
    def execute(lines):
        """Execute lines of Python code.
        
        Returns a deferred to tuple of (id, stdin, stdout, stderr).
        """
    
    def push(**namespace):
        """Push dict namespace into the user's namespace.
        
        Returns a deferred to None.
        """
    
    def pull(*keys):
        """Pulls values out of the user's namespace by keys.
        
        Returns a deferred to tuple or object.
        """
    
    def pullNamespace(*keys):
        """Pulls values by key from user's namespace as dict.
        
        Returns a defered to a dict."""
    
    def getResult(i=None):
        """Get the stdin/stdout/stderr of command i.
        
        Returns a deferred to a tuple."""
    
    def reset():
        """Reset the shell.
        
        This clears the users namespace.  But won't cause modules to be
        reloaded.
        """
    
    def kill():
        """Kill the engine by stopping the reactor."""
    
    def status():
        """Return the status of the engine.
        
        Returns a deferred to a dict."""
    

class IEngineSerialized(zi.Interface):
    """Push/Pull methods that take Serialized objects.  
    
    All methods should return deferreds.
    """
    
    def pushSerialized(**namespace):
        """Push a dict of keys and Serialized objects into the user's namespace."""
    
    def pullSerialized(*keys):
        """Pull objects by key from the user's namespace as Serialized.
        
        Returns a list of or one Serialized.
        """
    
    
class IEngineThreaded(zi.Interface):
    """A place holder for threaded commands.  
    
    All methods should return deferreds.
    """
    pass


class IEngineQueued(zi.Interface):
    """Interface for an Engine with a queue.  
    
    All methods should return deferreds.
    """
    
    def clearQueue():
        """Clear the queue."""
    

class IEngineComplete(IEngineBase, IEngineSerialized, IEngineQueued, IEngineThreaded):
    """An engine that implements everything.
    
    An "complete" engine is expected to implement IEngineBase, IEngineSerialized, 
    IEngine Queued, and IEngineThreaded.  
    
    All IEngine methods must return a deferred.  If a method is not implemented, 
    it is expected to return a deferred failing with NotImplementedError.
    """
    pass


#-------------------------------------------------------------------------------
# Functions and classes to implement the EngineService
#-------------------------------------------------------------------------------

def completeEngine(engine):
    """Completes an engine object.  
    
    The returned object is guaranteed to properly implement IEngineComplete.
    
    The methods that are not already implemented by engine are dynamically
    generated and will return a deferred to a NotImplementedError failure.
    """
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


class EngineService(object, service.Service):
    """Adapt a IPython shell into a IEngine implementing Twisted Service."""
    
    zi.implements(IEngineBase, IEngineSerialized)
                
    def __init__(self, shellClass, mpi=None):
        """Create an EngineService.
        
        shellClass: a subclass of core.InteractiveShell
        mpi:        an mpi module that has rank and size attributes
        """
        self.shell = shellClass()
        self.mpi = mpi
        self.id = None
        if self.mpi is not None:
            log.msg("MPI started with rank = %i and size = %i" % 
                (self.mpi.rank, self.mpi.size))
            self.id = self.mpi.rank
    
    # Make id a property so that the shell can get the updated id
        
    def _setID(self, id):
        self._id = id
        self.shell.update({'id': id})
        
    def _getID(self):
        return self._id
        
    id = property(_getID, _setID)
        
    def startService(self):
        """Start the service and seed the user's namespace."""
        
        self.shell.update({'mpi': self.mpi, 'id' : self.id})
            
    # The IEngine methods.  See the interface for documentation.
    
    def execute(self, lines):
        d = defer.execute(self.shell.execute, lines)
        d.addCallback(self.addIDToResult)
        return d

    def addIDToResult(self, result):
        return (self.id,) + result

    def push(self, **namespace):
        return defer.execute(self.shell.update, namespace)

    def pull(self, *keys):
        if len(keys) > 1:
            pulledDeferreds = []
            for key in keys:
                pulledDeferreds.append(defer.execute(self.shell.get,key))
            d = gatherBoth(pulledDeferreds)
            return d
        else:
            return defer.execute(self.shell.get, keys[0])
    
    def pullNamespace(self, *keys):
        ns = {}
        for key in keys:
            ns[key] = self.shell.get(key)
        return defer.succeed(ns)
    
    def getResult(self, i=None):
        d = defer.execute(self.shell.getCommand, i)
        d.addCallback(self.addIDToResult)
        return d
    
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

    def status(self):
        """Return the status of the Engine.
        
        This used to return a dict of all the keys/repr(values) in the 
        user's namespace.  This was too much info for the ControllerService
        to handle so it is now just a list of keys.
        """
        
        remotes = []
        for k in self.shell.locals.iterkeys():
            if k not in ['__name__', '__doc__', '__console__', '__builtins__']:
                remotes.append(k)
        return defer.succeed(remotes)

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
        return serialized.serialize(reason, 'FAILURE')
    
    
class QueuedEngine(object):
    """Add a queue to an IEngine implementing object.
    
    The resulting object will implement IEngineQueued.
    """
    
    zi.implements(IEngineQueued)
    
    def __init__(self, engine, keepUpToDate=False):
        """Create a QueuedEngine object from an engine
        
        keepUpToDate: whether to update the remote status when the 
                      queue is empty.  Defaults to False.
        """

        self.engine = engine
        self.id = engine.id
        self.queued = []
        self.history = {}
        self.engineStatus = {}
        self.upToDate = True
        self.keepUpToDate = keepUpToDate
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
    
    # methods from IEngineQueued:
    def clearQueue(self):
        """Clear the queue."""
        
        for cmd in self.queued:
            cmd.deferred.errback(failure.Failure(error.QueueCleared()))
        self.queued = []
        return defer.succeed(True)
    
    # Queue management methods.  You should not call these directly
    
    def submitCommand(self, cmd):
        """Submit command to queue."""
        
        d = defer.Deferred()
        cmd.setDeferred(d)
        self.upToDate = not self.keepUpToDate
        if self.currentCommand is not None:
            #log.msg("Queueing: " + repr(cmd))
            self.queued.append(cmd)
            return d
        self.currentCommand = cmd
        self.runCurrentCommand()
        return d
    
    def runCurrentCommand(self):
        """Run current command."""
        
        cmd = self.currentCommand
        # log.msg("Starting: " + repr(self.currentCommand))
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
        """Pop next command in queue and run it."""
        
        if len(self.queued) > 0:
            self.currentCommand = self.queued.pop(0)
            self.runCurrentCommand()
        elif not self.upToDate:
            d = self.submitCommand(Command('status'))
            self.upToDate = True
            return d.addCallbacks(self.updateStatus, util.catcher)
    
    def saveResult(self, result):
        """Put the result in the history."""
        
        self.history[result[1]] = result
        return result
    
    def finishCommand(self, result):
        """Finish currrent command."""
        
        # log.msg("Finishing: " + repr(self.currentCommand) + ':' + repr(result))
        self.currentCommand.handleResult(result)
        del self.currentCommand
        self.currentCommand = None
        self._flushQueue()
        return result
    
    def abortCommand(self, reason):
        """Abort current command."""
        
        self.currentCommand.handleError(reason)
        del self.currentCommand
        self.currentCommand = None
        self._flushQueue()
        return None
        #return reason
    
    def updateStatus(self, status):
        """The callback for keeping a local copy of the status."""
        
        self.engineStatus = status
    
    #methods from IEngineBase.  See IEngineBase for documentation.
    
    def reset(self):
        self.clearQueue()
        self.history = {}  # reset the cache - I am not sure we should do this
        return self.submitCommand(Command("reset"))
    
    def kill(self):
        self.clearQueue()
        return self.submitCommand(Command("kill"))
    
    def status(self):
        dikt = {'queue':map(repr,self.queued), 'pending':repr(self.currentCommand),
            'history':self.history}
        if self.keepUpToDate:
            dikt['engine'] = self.engineStatus
        return defer.succeed(dikt)
    
    def getResult(self, i=None):
        if i is None:
            i = max(self.history.keys()+[None])

        cmd = self.history.get(i, None)
        if cmd is None:
            return self.submitCommand(Command("getResult", i))
        else:
            return defer.succeed(cmd)
    
    
class Command(object):
    """A command object that encapslates queued commands.
    
    This class basically keeps track of a command that has been queued
    in a QueuedEngine.  It manages the deferreds and hold the method to be called
    and the arguments to that method.
    """
    
    
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
            args = str(self.args)[1:-2]  #cut off (...,)
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
        
        self.deferred.errback(reason)
    

