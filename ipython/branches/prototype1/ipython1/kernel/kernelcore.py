"""The Twisted core of the ipython kernel.

This module contains the Twisted protocols, factories, services, etc. used to
implement the ipython kernel.  This module only contains the network related
parts of the kernel.
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

from ipython1.core.shell import QueuedInteractiveConsole
from ipython1.core.shell import TrappingInteractiveConsole
from ipython1.startup import callback

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

class ResultReporterProtocol(protocol.DatagramProtocol):

    def __init__(self, result, addr):
        self.result = result
        self.addr = addr
        
    def startProtocol(self):
        package = pickle.dumps(self.result, 2)
        self.transport.write("RESULT %i %s" % (len(package), package), 
            self.addr)
        self.tried = True
        
    def datagramReceived(self,data, sending_addr):
        if sending_addr == self.addr and data == "RESULT OK":
            self.transport.stopListening()
            
class KernelTCPProtocol(basic.LineReceiver):

    def connectionMade(self):
        log.msg("Connection Made...")
        self.transport.setTcpNoDelay(True)
        self.state = 'init'
        self.work_vars = {}
        peer = self.transport.getPeer()
            
    #def sendLine(self, line):
    #    log.msg('S: ' + line)
    #    basic.LineReceiver.sendLine(self, line)
            
    def lineReceived(self, line):
        #log.msg('C: ' + line)
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
                    self.state = 'init'
                    self.reset_work_vars()

    # Copied from twisted.mail.imap4
    def rawDataReceived(self, data):
        passon = self._pendingLiteral.write(data)
        if passon is not None:
            self.setLineMode(passon) # should I reset the state here?
        
    def reset_work_vars(self):
        self.work_vars = {}
        
    def _reset(self):
        self.work_vars = {}
        self.state = 'init'
     
    #####   
    ##### The PUSH command
    #####
    
    def handle_init_PUSH(self, args):
    
        # Parse the args
        if not args:
            self.push_finish("FAIL")
            return
        else:
            args_str = args

        self.work_vars['push_name'] = args_str

        # Setup to process the command
        self.state = 'pushing'
        self.work_vars['current_ticket'] = self.factory.get_ticket()

    def setup_literal(self, size):
        """Called by data command handlers."""
        d = defer.Deferred()
        self._pendingLiteral = LiteralString(size, d)
        self.setRawMode()
        return d        

    def push_finish(self,msg):
        self.sendLine("PUSH %s" % msg)
        self._reset()
    
    def handle_pushing_PICKLE(self, size_str):
        try:
            size = int(size_str)
        except (ValueError, TypeError):
            self.push_finish("FAIL")
        else:         
            d = self.setup_literal(size)
            d.addCallback(self.process_pickle)

    def process_pickle(self, package):
        try:
            data = pickle.loads(package)
        except pickle.PickleError:
            self.push_finish("FAIL")
        else:
            # What if this fails?  When could it?
            self.factory.push(self.work_vars['push_name'],
                data, self.work_vars['current_ticket'])
            self.push_finish("OK")
    
    #####
    ##### The PULL command
    #####
    
    def handle_init_PULL(self, args):

        # Parse the args
        if not args:
            self.pull_finish("FAIL")
            return
        else:
            args_list = args.split(" ")

        pull_name = args_list[0]
        self.work_vars['pull_type'] = 'PICKLE'
        self.work_vars['current_ticket'] = self.factory.get_ticket()
        d = self.factory.pull(pull_name, self.work_vars['current_ticket'])
                
        d.addCallback(self.pull_ok)
        d.addErrback(self.pull_fail)
     
    def pull_ok(self, result):
        # Add error code here and chain the callbacks
        try:
            presult = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.pull_finish("FAIL")
        else:
            self.sendLine("PICKLE %s" % len(presult))
            self.transport.write(presult)
            self.pull_finish("OK")
           
    def pull_fail(self, failure):
        self.pull_finish("FAIL")

    def pull_finish(self, msg):
        self.sendLine("PULL %s" % msg)
        self._reset()

    #####
    ##### The RESULT command
    #####
    
    def handle_init_RESULT(self, args):

        if args is None:
            d = self.factory.get_last_result()
        else:
            try:
                cmd_num = int(args)
            except (ValueError, TypeError):
                self.result_finish("FAIL")
                return
            else:
                d = self.factory.get_result(cmd_num)
                                
        d.addCallback(self.result_ok)
        d.addErrback(self.result_fail)
     
    def result_ok(self, result):
        # Add error code here and chain the callbacks
        try:
            presult = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.result_finish("FAIL")
        else:
            self.sendLine("PICKLE %s" % len(presult))
            self.transport.write(presult)
            self.result_finish("OK")
           
    def result_fail(self, failure):
        self.result_finish("FAIL")

    def result_finish(self, msg):
        self.sendLine("RESULT %s" % msg)
        self._reset()

    #####
    ##### The EXECUTE command
    #####
    
    def handle_init_EXECUTE(self, args):
        """Handle the EXECUTE command."""
                
        # Parse the args
        if not args:
            self.execute_finish("FAIL")
            return
            
        if "BLOCK" in args:
            self.work_vars['execute_block'] = True
            execute_cmd = args[6:]
        else:
            self.work_vars['execute_block'] = False        
            execute_cmd = args
                 
        if not execute_cmd:
            self.execute_finish("FAIL")
            return
        
        if self.work_vars['execute_block']:
            #log.msg('Blocking execute')
            self.work_vars['current_ticket'] = self.factory.get_ticket()        
            d = self.factory.execute_block(execute_cmd,
                self.work_vars['current_ticket'])
            d.addCallback(self.execute_ok_block)
            d.addErrback(self.execute_fail)
        else:
            #log.msg('Blocking execute')                   
            self.execute_finish("OK")   
            # The deferToThread in this call costs 2 ms currently :(
            self.work_vars['current_ticket'] = self.factory.get_ticket()
            d = self.factory.execute(execute_cmd, 
                self.work_vars['current_ticket'])
            d.addCallback(self.execute_ok)
            d.addErrback(self.execute_fail)
        
    def execute_ok(self, result):
        for tonotify in self.factory.notifiers():
            reactor.listenUDP(0,ResultReporterProtocol(result, tonotify) )
                
    def execute_ok_block(self, result):
        try:
            package = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.execute_finish("FAIL")
        else:
            self.sendLine("PICKLE %i" % len(package))
            self.transport.write(package)
            self.execute_finish("OK")
            self.execute_ok(result)
        
    def execute_fail(self, f):
        pass
        
    def execute_finish(self, msg):
        self.sendLine("EXECUTE %s" % msg)
        self._reset()

    #####
    ##### Kernel control commands
    #####
    
    def handle_init_STATUS(self, args):
    
        status = self.factory.status()
        result = (status, self.state)    
                
        try:
            package = pickle.dumps(result, 2)
        except pickle.PickleError:
            self.sendLine('STATUS FAIL')
        else:
            self.sendLine("PICKLE %s" % len(package))
            self.transport.write(package)
            self.sendLine('STATUS OK')
        
    def handle_init_NOTIFY(self, args):
        args_split = args.split(" ")
        if len(args_split) == 3:
            action, host, port = args_split
            try:
                port = int(port)
            except (ValueError, TypeError):
                self.sendLine("NOTIFY FAIL")
            else:
                if action == "TRUE":
                    self.factory.add_notifier((host, port))
                    self.sendLine('NOTIFY OK')
                elif action == "FALSE":
                    self.factory.del_notifier((host, port))
                    self.sendLine('NOTIFY OK')
                else:
                    self.sendLine('NOTIFY FAIL')
        else:
            self.sendLine('NOTIFY FAIL')
    
    def handle_cluster_PICKLE(self, size_str):
        try:
            size = int(size_str)
        except (ValueError, TypeError):
            self.cluster_finish("FAIL")
        else:         
            d = self.setup_literal(size)
            d.addCallback(self.cluster_process_pickle)

    def cluster_process_pickle(self, package):
        try:
            data = pickle.loads(package)
        except pickle.PickleError:
            self.cluster_finish("FAIL")
        else:
            self.factory.create_cluster(data)
            self.cluster_finish("OK")        

    # The RESET, KILL and DISCONNECT commands

    def handle_RESET(self, args):
        log.msg("Resettng the kernel...")
        self.factory.reset()
        self.sendLine('RESET OK')
        self._reset()
        
    def handle_KILL(self, args):
        log.msg("Killing the kernel...")
        reactor.stop()
        
    def handle_DISCONNECT(self,args):
        log.msg("Disconnecting client...")
        self.sendLine("DISCONNECT OK")
        self.transport.loseConnection()
   
class KernelFactoryBase(protocol.ServerFactory):
    protocol = KernelTCPProtocol
    
    def __init__(self, notify=[], mpi=None):
        #log.msg("In __init__:")
        self._notifiers = notify
        self.mpi = mpi
        self.createShell()
        self.initMPI()
        
    def createShell(self):
        "set the self.shell attribute"
        raise NotImplemented("Use of sublcass of KernelFactory Base")
        
    def initMPI(self):
        "Use self.mpi to setup mpi in the users namespace"
        self.push('mpi', self.mpi)
        
    # Command notification addresses
        
    def notifiers(self):
        return self._notifiers
        
    def add_notifier(self, n):
        if n not in self._notifiers:
            self._notifiers.append(n)
        print "Notifiers: ", self._notifiers
            
    def del_notifier(self, n):
        if n in self._notifiers:
            del self._notifiers[self._notifiers.index(n)]
        print "Notifiers: ", self._notifiers
        
    
 
class KernelTCPFactory(KernelFactoryBase):
        
    def createShell(self):
        #log.msg('KernelTCPFactory.createShell')
        self.shell = QueuedInteractiveConsole()
        self.shell.start_work()          
        
    # Kernel methods
            
    def get_ticket(self):
        return self.shell.get_ticket()
        
    def push(self, key, value, ticket=None):
        self.shell.push(key, value, ticket)
        
    def pull(self, key, ticket):
        d = threads.deferToThread(self.shell.pull, key, ticket)
        return d
        
    def execute(self, source, ticket):
        #log.msg('KernelTCPFactory.execute')
        d = threads.deferToThread(self.shell.execute, source, ticket)
        return d
        
    def execute_block(self, source, ticket):
        #log.msg('KernelTCPFactory.execute')
        result = self.shell.execute(source, ticket, block=True)
        return defer.succeed(result)
        
    def status(self):
        return self.shell.status()
        
    def reset(self):
        self.shell.reset()
        
    def get_result(self, i):
        d = threads.deferToThread(self.shell.get_result, i)
        return d
        
    def get_last_result(self):
        d = threads.deferToThread(self.shell.get_last_result)
        return d
                
class ThreadlessKernelTCPFactory(KernelFactoryBase):
 
    def createShell(self):
        self.shell = TrappingInteractiveConsole()

    # Kernel methods
            
    def get_ticket(self):
        return 0
        
    def push(self, key, value, ticket=None):
        self.shell.update({key:value})
        
    def pull(self, key, ticket):
        data = self.shell.get(key)
        return defer.succeed(data)
        
    def execute(self, source, ticket):
        self.shell.runlines(source)
        result = self.shell.get_last_result()
        return defer.succeed(result)
        
    def execute_block(self, source, ticket):
        return self.execute(source=source, ticket=ticket)
        
    def status(self):
        return 0
        
    def reset(self):
        del self.shell
        self.shell = TrappingInteractiveConsole()
        
    def get_result(self, i):
        result = self.shell.get_result(i)
        return defer.succeed(result)
        
    def get_last_result(self):
        result = self.shell.get_last_result()
        return defer.succeed(result)
        
        
