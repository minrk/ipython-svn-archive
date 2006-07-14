"""process protocol and factory for incoming remote engine connections.
    classes:
        RemoteEngineProcessProtocol(protocol.ProcessProtocol)
        RemoteEngineProcessFactory(protocol.ServerFactory)

    At the moment, these do very little other than pass events to a service.    
"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from twisted.internet import protocol
from zope.interface import implements
from ipython1.kernel import networkinterfaces


class RemoteEngineProcessProtocol(protocol.ProcessProtocol):
    
    implements(networkinterfaces.IREProtocol)
    
    def __init__(self):
        pass
    
    def connectionMade(self):
        """Called when the RemoteEngines connect, relay event to factory.
        
        passes itself as argument for the engine object
        """
        
        self.id = self.factory.registerEngine(self)
    
    def outReceived(self, data):
        """Let the factory decide what to do."""
        
        self.factory.outReceived(self.engine.id, data)
    
    def errReceived(self, data):
        """Let the factory decide what to do."""
        
        self.factory.errReceived(self.engine.id, data)
    
    def processEnded(self, status):
        """Let the factory decide what to do."""
        
        self.factory.handleRemoteEngineProcessEnding(self.engine.id, status)
    

class RemoteEngineProcessFactory(protocol.ServerFactory):
    """factory that passes everything to service"""
    
    implements(networkinterfaces.IREFactory)
    
    protocol = RemoteEngineProcessProtocol
    def __init__(self):
        pass
    
    def outReceived(self, data):
        """Let the service decide what to do."""
        
        self.service.outReceived(self.engine.id, data)
    
    def errReceived(self, data):
        """Let the service decide what to do."""
        
        self.service.errReceived(self.engine.id, data)
    
    def processEnded(self, status):
        """Let the service decide what to do."""
        
        self.service.handleRemoteEngineProcessEnding(self.engine.id, status)
    
    def registerEngine(self, protocol):
        """Let the service decide what to do."""
        
        return self.service.registerEngine(protocol)
    
