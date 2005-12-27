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

try:
    from ipython1.kernel1p.console import QueuedInteractiveConsole,\
        TrappingInteractiveConsole
except ImportError:
    print "ipython1 needs to be in your PYTHONPATH"

# modified from twisted.mail.imap4.LiteralString
class LiteralString:
    def __init__(self, size, defered):
        self.size = size
        self.data = []
        self.defer = defered

    def write(self, data):
        self.size -= len(data)
        passon = None
        if self.size > 0:
            self.data.append(data)
        else:
            if self.size:
                data, passon = data[:self.size], data[self.size:]
            else:
                passon = ''
            if data:
                self.data.append(data)
            if passon == '':
                self.defer.callback(''.join(self.data))
        return passon

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
        
    #############################################
    #   Handlers for the protocol               #
    #############################################
    
    #############################################
    #   EXECUTE                                 #
    #############################################
    
    def handle_INIT_EXECUTE(self, args):
        """Handle the EXECUTE command in the INIT state."""
        
        if not args:
            self.execute_finish("FAIL")
            return
                   
        cmd = args
        log.msg("EXECUTE: %s" % cmd)
        
        # Execute the command
        try:
            result = self.factory.execute(cmd)
        except:
            self.execute_finish("FAIL")
            
        print result
        # Pickle the result dict and reply to client
        try:
            package = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.execute_finish("FAIL")
        else:
            self.sendLine("RESULT %i" % len(package))
            self.transport.write(package)
            self.execute_finish("OK")
            
    def execute_finish(self, msg):
        """Send final reply to the client and reset the protocol."""
        self.sendLine("EXECUTE %s" % msg)
        self._reset()

    #############################################
    #   PUSH                                    #
    #############################################

    def handle_INIT_PUSH(self, args):
        """Handle the PUSH command in the INIT state."""
        log.msg("PUSH %s" % msg)
        
        # Parse the args
        if not args:
            self.push_finish("FAIL")
            return
                                            
        self.state_vars['push_name'] = args

        # Setup to process the command
        self.state = 'PUSHING'

    def setup_literal(self, size):
        """Called by data command handlers to handle raw data."""
        d = defer.Deferred()
        self._pendingLiteral = LiteralString(size, d)
        self.setRawMode()
        return d        
        
    def handle_PUSHING_PICKLE(self, size_str):
        """Handle the PICKLE command in the PUSHING state.""" 
        try:
            size = int(size_str)
        except (ValueError, TypeError):
            self.push_finish("FAIL")
        else:         
            d = self.setup_literal(size)
            d.addCallback(self.process_pickle)

    def process_pickle(self, package):
        """Unpack a pickled package and put it in the users namespace."""
        try:
            data = pickle.loads(package)
        except pickle.PickleError:
            self.push_finish("FAIL")
        else:
            # What if this fails?  When could it?
            self.factory.push(self.work_vars['push_name'], data)
            self.push_finish("OK")

    def push_finish(self,msg):
        """Send final reply to the client and reset the protocol."""
        self.sendLine("PUSH %s" % msg)
        self._reset()

        self.sendLine("PUSH %s" % msg)
        self._reset()

    #############################################
    #   PULL                                    #
    #############################################

    def handle_INIT_PULL(self, msg):
        log.msg("PUSH %s" % msg)
        
    #############################################
    #         Misc                              #
    #############################################
    
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
    
    def __init__(self, allow=[], notify=[]):
        self.tic = TrappingInteractiveConsole()

    # Kernel methods
            
    def push(self, key, value):
        self.tic.update({key:value})
        
    def pull(self, key):
        value = self.tic.get(key)
        return value

    def execute(self, source):
        self.tic.runlines(source)
        result = self.tic.get_last_result()
        return result
        
    def reset(self):
        self.tic.locals = {}
        
    def get_result(self, i):
        return self.tic.get_result(i)
        
    def get_last_result(self):
        return self.tic.get_last_result()
        
    