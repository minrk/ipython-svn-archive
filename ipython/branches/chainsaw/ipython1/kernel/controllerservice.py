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

from ipython1.kernel.remoteengine import RemoteEngine, Command

# Interface for the Controller Service

class IControllerService(Interface):
    """The Interface for the IP Controller Service"""
    
    def registerEngine(self, remoteEngine):
        """register new remote engine"""
    
    def unregisterEngine(self, id):
        """eliminate remote engine object"""
    
    def reconnectEngine(self, id):
        """handle reconnecting engine"""
    
    def disconnectEngine(self, id):
        """handle disconnecting engine"""
    
    def submitCommand(self, cmd, id='all'):
        """submit command to engine(s)"""
    
    def tellAll(self, cmd):
        """submit command to all available engines"""
    
    def cleanQueue(self, id='all'):
        """Cleans out pending commands in an engine's queue."""
    
    def interruptEngine(self, id='all'):
        """Send SIGUSR1 to the kernel engine to stop the current command."""
    

#implementation of the Controller Service
        
class ControllerService(service.Service):
    """This service listens for kernel engines and control clients.
        It manages the command queues for the engines.
    """
    
    implements(IControllerService)
    
    def __init__(self, maxEngines=255, saveIDs=False):
        self.saveIDs = saveIDs
        self.engine = {}
        self.availableID = range(maxEngines,-1,-1)#[255,...,0]
    
    
    def registerEngine(self, remoteEngine):
        """register new engine connection"""
        id = self.availableID.pop()
        remoteEngine.service = self
        remoteEngine.id = id
        remoteEngine.setRestart(False)
        self.engine[id] = remoteEngine
        log.msg("registered engine %i" %id)
        return id
    
    def unregisterEngine(self, id):
        """eliminate remote engine object"""
        log.msg("unregistered engine %i" %id)
        e = self.engine.pop(id)
        del e
        if self.saveIDs:
            log.msg("preserving id %i" %id)
            self.availableID.append(id)
    
    def reconnectEngine(self, remoteEngine):
        """handle reconnecting engine"""
        #if we want to keep the engine, reconnect to it, for now get a new one|
        id = remoteEngine.id
        try:
            if self.engine[id] is 'restarting':
                remoteEngine.service = self
                remoteEngine.restart = True
                self.engine[id] = remoteEngine
                log.msg("reconnected engine %i" %id)
            else:
                raise Exception('illegal reconnect')
        except KeyError:
            raise Exception('illegal reconnect id')
    
    def disconnectEngine(self, id):
        """handle disconnecting engine"""
        #do I want to keep the RemoteEngine object or not?
        #for now, no
        log.msg("engine %i disconnected" %id)
        if self.engine[id].restart:
            log.msg("expecting reconnect")
            self.engine[id] = 'restarting'
        else:
            self.unregisterEngine(id)
    
    def submitCommand(self, cmd, id='all'):
        """submit command to engine(s)"""
        log.msg("submitting command: %s to %s" %(cmd, id))
        if id is not 'all':
            return self.engine[id].submitCommand(cmd)
        else:
            l = []
            for e in self.engine.values():
                if e is not 'restarting':
                    command = Command(cmd.remoteMethod, *cmd.args)
                    d = e.submitCommand(command)
                    l.append(d)
            return defer.gatherResults(l)
    

    def tellAll(self, cmd):
        """submit command to all available engines"""
        return self.submitCommand(cmd)
    
    def cleanQueue(self, id='all'):
        """Cleans out pending commands in the kernel's queue."""
        log.msg("cleaning queue %s" %id)
        if id is not 'all':
            self.engine[id].queued = []
        else:
            for e in self.engine.values():
                if e is not 'restarting':
                    e.queued = []
    
    def interruptEngine(self, id='all'):
        """Send SIGUSR1 to the kernel engine to stop the current command."""
        log.msg("(did not) interrupted engine %s" %id)
        if self.engine[id].currentCommand:
            pass
            #not implemented
    
