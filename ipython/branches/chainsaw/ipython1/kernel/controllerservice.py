"""A Twisted Service for the Controller

TODO:

- Use subclasses of pb.Error to pass exceptions back to the calling process.
- Deal more carefully with the failure modes of the kernel engine.  The
  PbFactory should be make to reconnect possibly.
- Add an XML-RPC interface
- Add an HTTP interface
- Security!!!!!
"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import cPickle as pickle

from twisted.application import service, internet
from twisted.internet import protocol, reactor, defer
from twisted.python import log
from zope.interface import Interface, implements
from twisted.spread import pb

from ipython1.kernel.engineservice import Command
from ipython1.kernel.kernelerror import *

# Interface for the Controller Service

class IRemoteController(Interface):
    """The Interface the controller exposes to remote engines"""
    
    def registerEngine(self, remoteEngine):
        """register new remote engine"""
    
    #not sure if this one should be exposed in the interface
    def disconnectEngine(self, id):
        """handle disconnecting engine"""
    

class IMultiEngine(Interface):
    """interface to multiple objects implementing IEngine"""
    
    #IQueuedEngine multiplexer methods
    def cleanQueue(self, id='all'):
        """Cleans out pending commands in an engine's queue."""
    
    #IEngine multiplexer methods
    def execute(self, lines, id='all'):
        """Execute lines of Python code."""
    
    def put(self, key, value, id='all'):
        """Put value into locals namespace with name key."""
    
    def putPickle(self, key, package, id='all'):
        """Unpickle package and put into the locals namespace with name key."""
    
    def get(self, key, id='all'):
        """Gets an item out of the self.locals dict by key."""
    
    def getPickle(self, key, id='all'):
        """Gets an item out of the self.locals dist by key and pickles it."""
    
    def update(self, dictOfData, id='all'):
        """Updates the self.locals dict with the dictOfData."""
    
    def updatePickle(self, dictPickle, id='all'):
        """Updates the self.locals dict with the pickled dict."""
    
    def reset(self, id='all'):
        """Reset the InteractiveShell."""
    
    def status(self, id='all'):
        """Return the status of engines"""

    def getCommand(self, i=None, id='all'):
        """Get the stdin/stdout/stderr of command i."""
    
    def getLastCommandIndex(self, id='all'):
        """Get the index of the last command."""
    

#the controller interface implements both IEngineController, IMultiEngine
class IController(IRemoteController, IMultiEngine):
    pass
    
#implementation of the Controller Service
        
class ControllerService(service.Service):
    """This service listens for kernel engines and control clients.
        It manages the command queues for the engines.
    """
    
    implements(IController)
    
    def __init__(self, maxEngines=255, saveIDs=False):
        self.saveIDs = saveIDs
        self.engine = {}
        self.availableID = range(maxEngines,-1,-1)#[255,...,0]
    
    
    def registerEngine(self, remoteEngine, id):
        """register new engine connection"""
        if id in self.engine.keys():
            raise IdInUse
            return
            
        if id in self.availableID:
            remoteEngine.id = id
            self.availableID.remove(id)
        else:
            id = self.availableID.pop()
            remoteEngine.id = id
            
        remoteEngine.service = self
        self.engine[id] = remoteEngine
        log.msg("registered engine %i" %id)
        return id
    
    def unregisterEngine(self, id):
        """eliminate remote engine object"""
        log.msg("unregistered engine %i" %id)
        del self.engine[id]
        if not self.saveIDs:
            self.availableID.append(id)
        else:
            log.msg("preserving id %i" %id)
    
    def disconnectEngine(self, id):
        """handle disconnecting engine"""
        #do I want to keep the RemoteEngine object or not?
        #for now, no
        log.msg("engine %i disconnected" %id)
        self.unregisterEngine(id)
    
    def engineList(self, id):
        """parse an id list into list of engines"""
        if type(id) is int:
            if id not in self.engine.keys():
                log.msg("id %i not registered" %i)
                return                
            return [self.engine[id]]
            
        if id is 'all':
            engines = self.engine.values()
        else:
            engines = []
            for i in id:
                if i in self.engine.keys():
                    engines.append(self.engine[i])
                else:
                    log.msg("id %i not registered" %i)
        return engines
    
    def keyList(self, id):
        """parse an id list into list of engine ids"""
        print id
        if type(id) is int:
            if id not in self.engine.keys():
                log.msg("id %i not registered" %i)
                return                
            return [id]
        if id is 'all':
            keys = self.engine.keys()
        else:
            keys = []
            for i in id:
                if i in self.engine.keys():
                    keys.append(i)
                else:
                    log.msg("id %i not registered" %i)
        return keys
    
    #IMultiEngine methods
    def cleanQueue(self, id='all'):
        """Cleans out pending commands in the kernel's queue."""
        log.msg("cleaning queue %s" %id)
        engines = self.engineList(id)
        if not engines:
            return defer.succeed(None)
        l = []
        for e in engines:
            l.append(e.cleanQueue())
        return defer.gatherResults(l)
    
    def execute(self, lines, id='all'):
        """Execute lines of Python code."""
        log.msg("executing %s on %s" %(lines, id))
        engines = self.engineList(id)
        l = []
        for e in engines:
            l.append(e.execute(lines))
        return defer.gatherResults(l)        
    
    def put(self, key, value, id='all'):
        """Put value into locals namespace with name key."""
        log.msg("putting %s=%s on %s" %(key, value, id))
        engines = self.engineList(id)
        l = []
        for e in engines:
            l.append(e.put(key, value))
        return defer.gatherResults(l)
    
    def putPickle(self, key, package, id='all'):
        """Unpickle package and put into the locals namespace with name key."""
        log.msg("putting pickle %s=%s on %s" %(key, pickle.loads(package), id))
        engines = self.engineList(id)
        l = []
        for e in engines:
            l.append(e.putPickle(key, package))
        return defer.gatherResults(l)
    
    def get(self, key, id='all'):
        """Gets an item out of the self.locals dict by key."""
        log.msg("getting %s from %s" %(key, id))
        engines = self.engineList(id)
        l = []
        for e in engines:
            l.append(e.get(key))
        return defer.gatherResults(l)
    
    def getPickle(self, key, id='all'):
        """Gets an item out of the self.locals dist by key and pickles it."""
        log.msg("getting pickle %s from %s" %(key, id))
        engines = self.engineList(id)
        l = []
        for e in engines:
            l.append(e.getPickle(key))
        return defer.gatherResults(l)
    
    def update(self, dictOfData, id='all'):
        """Updates the self.locals dict with the dictOfData."""
        log.msg("updating %s with %s" %(id, dict))
        engines = self.engineList(id)
        l = []
        for e in engines:
            l.append(e.update(dictOfData))
        return defer.gatherResults(l)
    
    def updatePickle(self, dictPickle, id='all'):
        """Updates the self.locals dict with the pickled dict."""
        log.msg("updating %s with pickle %s" %(id, pickle.loads(dictPickle)))
        engines = self.engineList(id)
        l = []
        for e in engines:
            l.append(e.updatePickle(dictPickle))
        return defer.gatherResults(l)
    
    def status(self, id='all'):
        log.msg("retrieving status of %s" %id)
#        if id is None:
#            return self.engine.keys()
        keys = self.keyList(id)
        d = {}
        for k in keys:
            d[k] = self.engine[k].status()
        return d
        
    def reset(self, id='all'):
        """Reset the InteractiveShell."""
        log.msg("resetting %s" %(id))
        engines = self.engineList(id)
        l = []
        for e in engines:
            l.append(e.reset())
        return defer.gatherResults(l)
    
    def kill(self, id='all'):
        log.msg("resetting %s" %(id))
        engines = self.engineList(id)
        l = []
        for e in engines:
            l.append(e.kill())
        return defer.gatherResults(l)
        
    def getCommand(self, i=None, id='all'):
        """Get the stdin/stdout/stderr of command i."""
        log.msg("getting command %s from %s" %(i, id))
        engines = self.engineList(id)
        l = []
        for e in engines:
            l.append(e.getCommand(i))
        return defer.gatherResults(l)
    
    def getLastCommandIndex(self, id='all'):
        """Get the index of the last command."""
        log.msg("getting last command index from %s" %(id))
        engines = self.engineList(id)
        l = []
        for e in engines:
            l.append(e.getLastCommandIndex())
        return defer.gatherResults(l)
    

