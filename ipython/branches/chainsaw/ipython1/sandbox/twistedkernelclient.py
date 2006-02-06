"""This is a messy , unworking draft of a Twisted based kernel client
for the one process kernel.  It does have important ideas that are worth
keeping though. 

B. Granger  
02/05/06
"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************
import cPickle as pickle

from twisted.internet import protocol, reactor, threads, defer
from twisted.protocols import basic
from twisted.python.runtime import seconds
from twisted.python import log
from twisted.python import failure
import sys


from twisted.python.components import Interface
from zope.interface import implements
        
class PushCommand:
        
    def __init__(self, key, value):
        self.key = key
        self.value = value
                
    def setDeferred(self, d):
        self.deferred = d
        
    def setProtocol(self, p):
        self.protocol = p
                
    def sendInitial(self):
        try:
            package = pickle.dumps(value, 2)
        except picket.PickleError, e:
            return defer.fail()

        self.protocol.sendLine("PUSH %s" % key)
        self.protocol.sendLine("PICKLE %i" % len(package))
        self.protocol.transport.write(package)
        self.state = "PUSHING"
        
    def lineReceived(self, line):
        """Called when a line is received and this command is active."""

        if line == "PUSH OK":
            self.finishCommand(True)
    
    def rawDataReceived(self, data):
        """Called when raw data is received and this command is active."""
        pass    
 
    def finishCommand(self, result):
        self.deferred.callback(result)
    

class KernelClientTCPProtocol(basic.LineReceiver):

    queued = None
    currentCommand = None

    def __init__(self):

        self.queued = []

    def connectionMade(self):
        log.msg("Connection Made...")
        self.transport.setTcpNoDelay(True)

    def lineReceived(self, line):
        print 'S: ' + repr(line)
        
        if self.currentCommand is not None:
            self.currentCommand.lineReceived(line)
        else:
            self.transport.loseConnection()
            
    def rawDataReceived(self, data):
        print 'S: ' + repr(data)
        
        if self.currentCommand is not None:
            self.currentCommand.rawDataReceived(data)
        else:
            self.transport.loseConnection()    
    
    def _flushQueue(self):
        if self.queued:
            self.currentCommand = self.queued.pop(0)
            self.currentCommand.sendInitial()

    def sendCommand(self, cmd):
        
        d = defer.Deferred()
        cmd.setDeferred(d)
        cmd.setProtocol(self)
        if self.currentCommand is not None:
            self.queued.append(cmd)
            return d
        self.currentCommand = cmd
        self.currentCommand.sendInitial()
        return d

    def finalizeCommand(self, result):
        del self.currentCommand
        self.currentCommand = None
        self._flushQueue()
        return result
            
    #####   
    ##### Actual user commands
    #####
            
    def push(self, key, value):
        """Push something, return a deferred."""
        
        d = self.sendCommand(PushCommand(key, value))
        d.addCallback(self.finalizeCommand)
        return d
        
    def pull(self, key):
        """Pull something, return a deferred."""
        pass
        
    def execute(self, source):
        """Execute something, return a deferred."""
        pass


class KernelClientTCPFactory(protocol.ClientFactory):
    protocol = KernelClientTCPProtocol

    def clientConnectionFailed(self, connector, reason):
        print 'connection failed:', reason.getErrorMessage()
        reactor.stop()

    def clientConnectionLost(self, connector, reason):
        print 'connection lost:', reason.getErrorMessage()
        reactor.stop()
