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


from twisted.application import service, internet
from twisted.internet import protocol, reactor, defer
from twisted.python import log
from zope.interface import Interface, implements
from twisted.spread import pb

from ipython1.kernel.engineservice import Command

# Interface for the Controller Service

class IController(Interface):
    """The Interface for the IP Controller Service"""
    
    def registerEngine(self, remoteEngine):
        """register new remote engine"""
    
    def unregisterEngine(self, id):
        """eliminate remote engine object"""
    
    def reconnectEngine(self, id):
        """handle reconnecting engine"""
    
    def disconnectEngine(self, id):
        """handle disconnecting engine"""
    
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
    
    def getCommand(self, i=None, id='all'):
        """Get the stdin/stdout/stderr of command i."""
    
    def getLastCommandIndex(self, id='all'):
        """Get the index of the last command."""
    

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
            raise 'id in use'
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
        e = self.engine.pop(id)
        del e
    
    def disconnectEngine(self, id):
        """handle disconnecting engine"""
        #do I want to keep the RemoteEngine object or not?
        #for now, no
        log.msg("engine %i disconnected" %id)
        if not self.saveIDs:
            self.availableID.append(id)
        else:
            log.msg("preserving id %i" %id)
        self.unregisterEngine(id)
    
    def submitCommand(self, cmd, id='all'):
        """submit command to engine(s)"""
        log.msg("submitting command: %s to %s" %(cmd, id))
        if id is not 'all':
            return self.engine[id].submitCommand(cmd)
        else:
            l = []
            for e in self.engine.values():
                command = Command(cmd.remoteMethod, *cmd.args)
                d = e.submitCommand(command)
                l.append(d)
            return defer.gatherResults(l)
    
    def cleanQueue(self, id='all'):
        """Cleans out pending commands in the kernel's queue."""
        log.msg("cleaning queue %s" %id)
        if id is not 'all':
            self.engine[id].queued = []
        else:
            for e in self.engine.values():
                e.queued = []
    
    #IEngine multiplexer methods
    def execute(self, lines, id='all'):
        """Execute lines of Python code."""
        log.msg("executing %s on %s" %(lines, id))
        if type(id) is int:
            return self.engine[id].execute(lines)
            
        if id is 'all':
            engines = self.engine.keys()
        else:
            engines = []
            for i in id:
                engines.append(self.engine[i])
        l = []
        for e in engines:
            d = e.execute(lines)
            l.append(d)
            return defer.gatherResults(l)
        
    
    def put(self, key, value, id='all'):
        """Put value into locals namespace with name key."""
        log.msg("putting %s=%s on %s" %(key, value, id))
        if type(id) is int:
            return self.engine[id].put(key, value)
            
        if id is 'all':
            engines = self.engine.keys()
        else:
            engines = []
            for i in id:
                engines.append(self.engine[i])
        l = []
        for e in engines:
            d = e.put(key, value)
            l.append(d)
            return defer.gatherResults(l)
    
    def putPickle(self, key, package, id='all'):
        """Unpickle package and put into the locals namespace with name key."""
        log.msg("putting pickle %s=%s on %s" %(key, value, id))
        if type(id) is int:
            return self.engine[id].putPickle(key, value)
            
        if id is 'all':
            engines = self.engine.keys()
        else:
            engines = []
            for i in id:
                engines.append(self.engine[i])
        l = []
        for e in engines:
            d = e.putPickle(key, value)
            l.append(d)
            return defer.gatherResults(l)
    
    def get(self, key, id='all'):
        """Gets an item out of the self.locals dict by key."""
        log.msg("getting %s from %s" %(key, id))
        if type(id) is int:
            return self.engine[id].get(key)
            
        if id is 'all':
            engines = self.engine.keys()
        else:
            engines = []
            for i in id:
                engines.append(self.engine[i])
        l = []
        for e in engines:
            d = e.get(key)
            l.append(d)
            return defer.gatherResults(l)
    
    def getPickle(self, key, id='all'):
        """Gets an item out of the self.locals dist by key and pickles it."""
        log.msg("getting pickle %s from %s" %(key, id))
        if type(id) is int:
            return self.engine[id].getPickle(key)
            
        if id is 'all':
            engines = self.engine.keys()
        else:
            engines = []
            for i in id:
                engines.append(self.engine[i])
        l = []
        for e in engines:
            d = e.getPickle(key)
            l.append(d)
            return defer.gatherResults(l)
    
    def update(self, dictOfData, id='all'):
        """Updates the self.locals dict with the dictOfData."""
        log.msg("updating %s with %s" %(id, dict))
        if type(id) is int:
            return self.engine[id].update(dictOfData)
            
        if id is 'all':
            engines = self.engine.keys()
        else:
            engines = []
            for i in id:
                engines.append(self.engine[i])
        l = []
        for e in engines:
            d = e.update(dictOfData)
            l.append(d)
            return defer.gatherResults(l)
    
    def updatePickle(self, dictPickle, id='all'):
        """Updates the self.locals dict with the pickled dict."""
        log.msg("updating %s with pickle %s" %(id, dictPickle))
        if type(id) is int:
            return self.engine[id].updatePickle(dictPickle)
            
        if id is 'all':
            engines = self.engine.keys()
        else:
            engines = []
            for i in id:
                engines.append(self.engine[i])
        l = []
        for e in engines:
            d = e.updatePickle(dictPickle)
            l.append(d)
            return defer.gatherResults(l)
    
    def reset(self, id='all'):
        """Reset the InteractiveShell."""
        log.msg("resetting %s" %(id))
        if type(id) is int:
            return self.engine[id].reset()
            
        if id is 'all':
            engines = self.engine.keys()
        else:
            engines = []
            for i in id:
                engines.append(self.engine[i])
        l = []
        for e in engines:
            d = e.reset()
            l.append(d)
            return defer.gatherResults(l)
    
    def getCommand(self, i=None, id='all'):
        """Get the stdin/stdout/stderr of command i."""
        log.msg("getting command %s from %s" %(i, id))
        if type(id) is int:
            return self.engine[id].getCommand(i)
            
        if id is 'all':
            engines = self.engine.keys()
        else:
            engines = []
            for i in id:
                engines.append(self.engine[i])
        l = []
        for e in engines:
            d = e.getCommand(i)
            l.append(d)
            return defer.gatherResults(l)
    
    def getLastCommandIndex(self, id='all'):
        """Get the index of the last command."""
        log.msg("getting last command index from %s" %(id))
        if type(id) is int:
            return self.engine[id].getLastCommandIndex()
            
        if id is 'all':
            engines = self.engine.keys()
        else:
            engines = []
            for i in id:
                engines.append(self.engine[i])
        l = []
        for e in engines:
            d = e.getLastCommandIndex()
            l.append(d)
            return defer.gatherResults(l)
    

