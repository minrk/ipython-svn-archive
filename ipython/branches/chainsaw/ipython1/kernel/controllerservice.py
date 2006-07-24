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
                e.queued = []
    
    def interruptEngine(self, id='all'):
        """Send SIGUSR1 to the kernel engine to stop the current command."""
        log.msg("(did not) interrupted engine %s" %id)
        if self.engine[id].currentCommand:
            pass
            #not implemented
    
