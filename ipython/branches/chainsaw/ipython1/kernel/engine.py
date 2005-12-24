"""The Twisted related parts of the Kernel Engine."""
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

class KernelEngineProtocol(basic.LineReceiver):
    """Network protocol for the kernel engine."""

    def connectionMade(self):
        """Setup per connection things."""
        log.msg("Connection Made...")
        self.transport.setTcpNoDelay(True)
        self.state = 'INIT'
        self.state_vars = {}

    def lineReceived(self, line):
        """Called when a line is received.
        
        This method implements the main parts of the kernel engine
        protocol.  It works by analysing the received line and calling
        the appropriate handler method.  The analysis of the line is based on
        two things:
        
            1. The current state of the protocol (INIT, PULLING, etc.)
            2. The command (first word) of the received line 
              (KILL, STATUS, etc.)
            
        The handlers are named according to the following convention:
        
        handle[_state][_command]
        
        The handlers are resolved accoring to the follow precidence:
        
            1.  Handler resolved by both state and command.
            2.  Handler resolved by command only.
            3.  Handler resolved by state only.
            4.  Handler not resolved (default handler called).

        @arg line: The line that has been received.
        @type line: str
        """
        split_line = line.split(" ", 1)
        if len(split_line) == 1:
            cmd = split_line[0]
            args = None
        elif len(split_line) == 2:
            cmd = split_line[0]
            args = split_line[1]

        f = getattr(self, 'handle_%s_%s' %
                    (self.state, cmd), None)            
        if f:
            # Handler resolved with state and cmd 
            f(args)
        else:
            f = getattr(self, 'handle_%s' %
                (cmd), None)
            if f:
                # Handler resolved with only cmd
                f(args)
            else:
                f = getattr(self, 'handle_%s' %
                    (self.state), None)
                if f:
                    # Handler resolve with only self.state
                    # Pass the entire line rather than just args
                    f(line)
                else:
                    # No handler resolved
                    self.sendLine("BAD")
                    self._reset()

    def reset_state_vars(self):
        """Reset the state variables."""
        self.state_vars = {}
        
    def _reset(self):
        """Fully reset the state of the protocol."""
        self.reset_state_vars()
        self.state = 'INIT'
        
    ########
    ########  Handlers for the protocol
    ########
    
    def handle_INIT_EXECUTE(self, args):
        """Handle the EXECUTE command in the state INIT."""
        
        if not args:
            self.execute_finish("FAIL")
            return
                   
        cmd = args
        log.msg("EXECUTE: %s" % cmd)
        #result = self.factory.execute(cmd)
            
        self.execute_finish("OK")
            
    def execute_finish(self, msg):
        """Send final reply to the client and reset the protocol."""
        self.sendLine("EXECUTE %s" % msg)
        self._reset()

    def handle_KILL(self, args):
        log.msg("Killing the kernel...")
        reactor.stop()

    def handle_DISCONNECT(self, args):
        log.msg("Disconnecting client...")
        self.sendLine("DISCONNECT OK")
        self.transport.loseConnection()
    
class KernelEngineFactory(protocol.ServerFactory):
    """Factory for creating KernelEngineProtocol instances."""
    
    protocol = KernelEngineProtocol
    
    def __init__(self):
        pass
        
    