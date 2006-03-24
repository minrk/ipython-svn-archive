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
from twisted.python import failure
        
class ProtocolError(Exception):
    pass
    
class KernelCommandError(Exception):
    pass
    
class LiteralString:
    def __init__(self, size, deferred):
        self.size = size
        self.data = []
        self.deferred = deferred

    def write(self, data):
        self.size -= len(data)
        extra = None
        if self.size > 0: # We need more so just append everything
            self.data.append(data)
            done = False
        else:  # We have exactly enough or too much
            if self.size: # We have too much
                data, extra = data[:self.size], data[self.size:]
            else:  # We have just enough
                extra = ''
            if data: # Append just the right amount
                self.data.append(data)
            self.deferred.callback(''.join(self.data))
            done = True
        return done, extra
            
class Command(object):

    command = None

    def setDeferred(self, d):
        """Sets the deferred attribute of the Command."""
        self.deferred = d
        
    def setProtocol(self, p):
        """Sets the protocol that is using the Command."""
        self.protocol = p
                
    def sendInitial(self):
        """Called after the command is created."""
        pass
                
    def _parseLine(self, line):
        split_line = line.split(" ", 1)
        if len(split_line) == 1:
            cmd = split_line[0]
            args = None
        elif len(split_line) == 2:
            cmd = split_line[0]
            args = split_line[1]
        else:
            self.deferred.errback(ProtocolError())
            
        return cmd, args        
                
    def lineReceived(self, line):
        """Called when a line is received and this command is active."""
        
        # Parse the line into the form "cmd args"
        cmd, args = self._parseLine(line)
                    
        # Resolve with both state and cmd
        f = getattr(self, 'handle_%s_%s' %
                    (self.state, cmd), None)
        if f:
            f(args)   # only pass on the args
        else:
            # Now just by state
            f = getattr(self, 'handle_%s' % (self.state), None)
            if f:
                f(line)   # pass on the entire line
            else:
                self.deferred.errback(ProtocolError())
            
    def rawDataReceived(self, data):
        """Called when raw data is received and this command is active."""
        try:
            done, extra = self._pendingLiteral.write(data)
        except AttributeError:
            self.deferred.errback(ProtocolError())
        else:
            if done:
                self.protocol.setLineMode(extra)   
 
    def setup_literal(self, size):
        """Called by data command handlers."""
        d = defer.Deferred()
        self._pendingLiteral = LiteralString(size, d)
        self.protocol.setRawMode()
        return d      
 
    def handle_default(self, line):
        self.deferred.errback(ProtocolError())

class SimpleCommand(Command):

    def handle_SENT(self, line):
        cmd, args = self._parseLine(line)
        if cmd == self.command:
            if args == "OK":
                self.deferred.callback(None)
            else:
                self.deferred.errback(KernelCommandError())
        else:
            self.deferred.errback(ProtocolError())
           
class DataCommand(Command):

    data = None

    def __init__(self, key):
        self.key = key
        self.state = "INIT"
                
    def handle_SENT_PICKLE(self, args):
        args_len = int(args)
        d = self.setup_literal(args_len)
        d.addCallback(self.process_pickle)
         
    def handle_SENT(self, line):
        cmd, args = self._parseLine(line)
        if cmd == self.command:
            if args == "OK":
                if self.data is not None:   
                    self.deferred.callback(self.data)
                else:
                    self.deferred.errback(ProtocolError())
            else:
                self.deferred.errback(KernelCommandError())
        else:
            self.deferred.errback(ProtocolError())
            
    def process_pickle(self, package):
        try:
            self.data = pickle.loads(package)
        except pickle.PickleError, e:
            self.deferred.errback()
            
# Commands with a simple return

class PushCommand(SimpleCommand):
        
    command = 'PUSH'
        
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.state = "INIT"
                
    def sendInitial(self):
        try:
            package = pickle.dumps(self.value, 2)
        except pickle.PickleError, e:
            self.deferred.errback()

        self.protocol.sendLine("PUSH %s" % self.key)
        self.protocol.sendLine("PICKLE %i" % len(package))
        self.protocol.transport.write(package)
        self.state = "SENT"
                    
class AllowCommand(SimpleCommand):
    
    command = 'ALLOW'

    def __init__(self, ip):
        self.ip = ip
        self.state = "INIT"
        
    def sendInitial(self):
        self.protocol.sendLine("ALLOW TRUE %s" % self.ip)
        self.state = "SENT"
                
class DenyCommand(SimpleCommand):

    command = 'ALLOW'    

    def __init__(self, ip):
        self.ip = ip
        self.state = "INIT"
        
    def sendInitial(self):
        self.protocol.sendLine("ALLOW FALSE %s" % self.ip)
        self.state = "SENT"
    
class NotifyCommand(SimpleCommand):

    command = 'NOTIFY'

    def __init__(self, addr=None, flag=True):
        self.addr = addr
        self.flag = True
        self.state = "INIT"
        
    def sendInitial(self):
        if self.addr == None:
            host = socket.gethostbyname(socket.gethostname())
            port = 10104
            print "Kernel notification: ", host, port, flag
        else:
            host, port = self.addr
            
        if self.flag:
            self.protocol.sendLine("NOTIFY TRUE %s %s" % (host, port))
        else:
            self.protocol.sendLine("NOTIFY FALSE %s %s" % (host, port))
        self.state = "SENT"
            
class ClusterCommand(SimpleCommand):
    
    command = 'CLUSTER'
    
    def __init__(self, addrs=None):
        self.addrs = addrs
        
    def sendInitial(self):
        if self.addrs is None:
            self.protocol.sendLine("CLUSTER CLEAR")
        else:
            try:
                package = pickle.dumps(self.addrs, 2)
            except pickle.PickleError, e:
                self.deferred.errback()
            else:
                self.protocol.sendLine("CLUSTER CREATE")
                self.protocol.sendLine("PICKLE %i" % len(package))
                self.protocol.sendLine(package)
                self.state = "SENT"
    
class ResetCommand(SimpleCommand):

    command = 'RESET'

    def __init__(self):
        self.state = "INIT"
        
    def sendInitial(self):
        self.protocol.sendLine("RESET")
        self.state = "SENT"
        
class KillCommand(SimpleCommand):

    command = 'KILL'

    def __init__(self):
        self.state = "INIT"
        
    def sendInitial(self):
        self.protocol.sendLine("KILL")
        self.protocol.transport.loseConnection()
        self.deferred.callback(True)

# Data commands
        
class PullCommand(DataCommand):

    command = 'PULL'

    def __init__(self, key):
        self.key = key
        self.state = "INIT"
        
    def sendInitial(self):
        self.protocol.sendLine("PULL %s" % self.key)
        self.state = "SENT"
         
class ResultCommand(DataCommand):

    command = 'RESULT'

    def __init__(self, number=None):
        self.number = number
        self.state = "INIT"
        
    def sendInitial(self):
        if self.number is not None:
            try:
                self.protocol.sendLine("RESULT %i" % self.number)
            except TypeError:
                self.deferred.errback()
        else:
            self.protocol.sendLine("RESULT")     
        self.state = "SENT"
 
class ExecuteCommand(DataCommand):
    
    command = 'EXECUTE'
    
    def __init__(self, cmd, block=False):
        self.cmd = cmd
        self.block = block
        self.state = "INIT"
        
    def sendInitial(self):
        if self.block:
            self.protocol.sendLine("EXECUTE BLOCK %s" % self.cmd)
        else:
            self.protocol.sendLine("EXECUTE %s" % self.cmd)
        self.state = "SENT"
     
    def handle_SENT(self, line):
        cmd, args = self._parseLine(line)
        if cmd == self.command:
            if args == "OK":
                if self.block:
                    if self.data is not None:
                        self.deferred.callback(self.data)
                    else:
                        self.deferred.errback(ProtocolError())
                else:
                    self.deferred.callback(None)
            else:
                self.deferred.errback(KernelCommandError())
        else:
            self.deferred.errback(ProtocolError())
                        
class StatusCommand(DataCommand):
    
    command = 'STATUS'
    
    def __init__(self):
        self.state = "INIT"
        
    def sendInitial(self):
        self.protocol.sendLine("STATUS")
        self.state = "SENT"
     
class DisconnectCommand(Command):

    command = 'DISCONNECT'

    def __init__(self):
        self.state = "INIT"
        
    def sendInitial(self):
        self.protocol.sendLine("DISCONNECT")
        self.state = "SENT"
        
    def handle_SENT(self, line):
        cmd, args = self._parseLine(line)
        if cmd == self.command:
            if args == "OK":
                self.deferred.callback(None)
                self.protocol.transport.loseConnection()
            else:
                self.deferred.errback(KernelCommandError())
        else:
            self.deferred.errback(ProtocolError())

class KernelClientTCPProtocol(basic.LineReceiver):

    def __init__(self):
        self.queued = []
        self.currentCommand = None

    def test(self):
        
        def printer(x):
            print "Result: ", x

        d = self.push('a',10)
        d.addCallback(printer)
        
        d = self.status()
        d.addCallback(printer)
        
        d = self.execute('print a',block=False)
        d.addCallback(printer)
        
        d = self.pull('a')
        d.addCallback(printer)
        
        d = self.result()
        d.addCallback(printer)
        
        d = self.result(0)
        d.addCallback(printer)                

        d = self.allow('129.210.112.39')
        d.addCallback(printer)
        
        d = self.deny('129.210.112.39')
        d.addCallback(printer)

        d = self.notify(('129.210.112.39',10106),True)
        d.addCallback(printer)       
        
        d = self.notify(('129.210.112.39',10106),False)
        d.addCallback(printer)
        
        d = self.reset()
        d.addCallback(printer)
        
        d = self.pull('a')
        d.addCallback(printer)
        
        d = self.disconnect()
        d.addCallback(printer)                 

    def connectionMade(self):
            
        log.msg("Connection Made...")
        self.transport.setTcpNoDelay(True)

        #self.test()
                
    def sendLine(self, line):
        print "C: " + repr(line)
        basic.LineReceiver.sendLine(self,line)

    def lineReceived(self, line):
        print 'S: ' + repr(line)
        
        if self.currentCommand is not None:
            self.currentCommand.lineReceived(line)
        else:
            log.msg("Unexpected kernel reply: ", line)
            self.transport.loseConnection()
            
    def rawDataReceived(self, data):
        print 'S: ' + repr(data)
        
        if self.currentCommand is not None:
            self.currentCommand.rawDataReceived(data)
        else:
            log.msg("Unexpected kernel reply: ", line)
            self.transport.loseConnection()

    def _flushQueue(self):
 
        if len(self.queued) > 0:
            self.currentCommand = self.queued.pop(0)
            self.currentCommand.sendInitial()
            #print "Starting: ", self.currentCommand
        
    def sendCommand(self, cmd):
        
        #print "Initiating: ", cmd
        d = defer.Deferred()
        d.addCallback(self.finalizeCommand)
        d.addErrback(self.abortCommand)
        cmd.setDeferred(d)
        cmd.setProtocol(self)
        if self.currentCommand is not None:
            #print "Queueing: ", cmd
            self.queued.append(cmd)
            return d
        #print "Starting: ", cmd
        self.currentCommand = cmd
        self.currentCommand.sendInitial()

        return d

    def finalizeCommand(self, result):
        #print "Finishing: ", self.currentCommand
        del self.currentCommand
        self.currentCommand = None
        self._flushQueue()
        return result
        
    def abortCommand(self, reason):
        print self.currentCommand
        reason.printTraceback()
        del self.currentCommand
        self.currentCommand = None
        self._flushQueue()
        return reason
            
    #####   
    ##### Actual user commands
    #####
            
    def push(self, key, value):
        """Push something, return a deferred."""
        
        d = self.sendCommand(PushCommand(key, value))
        return d
        
    def pull(self, key):
        """Pull something, return a deferred."""
        d = self.sendCommand(PullCommand(key))
        return d

    def result(self, number=None):
        """Pull something, return a deferred."""
        d = self.sendCommand(ResultCommand(number))
        return d
        
    def execute(self, cmd, block=False):
        """Execute something, return a deferred."""
        d = self.sendCommand(ExecuteCommand(cmd, block))
        return d

    def status(self):
        d = self.sendCommand(StatusCommand())
        return d

    def allow(self, ip):
        d = self.sendCommand(AllowCommand(ip))
        return d
        
    def deny(self, ip):
        d = self.sendCommand(DenyCommand(ip))
        return d
        
    def notify(self, addr=None, flag=True):
        d = self.sendCommand(NotifyCommand(addr, flag))
        return d

    def cluster(self, addrs=None):
        d = self.sendCommand(ClusterCommand(addrs))
        return d

    def reset(self):
        d = self.sendCommand(ResetCommand())
        return d
        
    def kill(self):
        d = self.sendCommand(KillCommand())
        return d
        
    def disconnect(self):
        d = self.sendCommand(DisconnectCommand())
        return d

class KernelClientTCPFactory(protocol.ClientFactory):
    protocol = KernelClientTCPProtocol

    def clientConnectionFailed(self, connector, reason):
        print 'connection failed:', reason.printTraceback()

    def clientConnectionLost(self, connector, reason):
        print 'connection lost:', reason.printTraceback()

class RemoteKernel(object):

    def __init__(self, addr):
        self.addr = addr
    
    def _connect(self):
        self.factory = KernelClientTCPFactory()
        self.connector = reactor.connectTCP(self.addr[0],
            self.addr[1],self.factory)
        self.protocol = self.connector.transport.protocol
        print self.protocol    
    
    def execute(self, cmd, block=False):
        d = self.protocol.execute(cmd,block)
        w = defer.waitForDeferred(d)
        yield w
        w = w.getResult()        

def main():
    f = KernelClientTCPFactory()
    reactor.connectTCP("localhost",10105,f)
    reactor.run()
    
if __name__ == "__main__":
    main()