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

class Mover(basic.LineReceiver):

    def connectionMade(self):
        self.transport.setTcpNoDelay(True)
        self.state = 'init'
        
    def push(self, key, data_pickle):
        self.d = defer.deferred()
        self.sendLine("PUSH %s" % key)
        self.sendLine("PICKLE %s" % len(self.data_pickle))
        self.transport.write(self.data_pickle)
        self.state = 'PUSH'
        return self.d
     
    def lineReceived(self, line):
        line_split = line.split(" ")
        if line_split[0] == self.state and line_split[1] == "OK":
            self.d.callback(True)
        else:
            self.d.callback(False)
        self.transport.loseConnection()
            
class KernelTCPProtocol(basic.LineReceiver):

    def connectionMade(self):
        log.msg("Connection Made...")
        self.transport.setTcpNoDelay(True)
        self.state = 'init'
        self.work_vars = {}
        peer = self.transport.getPeer()
        # I have turned off the ip address based secutiry because it is crap!
        #if not self.factory.is_allowed(peer.host):
        #    log.msg("Denied Client: %s" % peer.host)
        #    self.transport.loseConnection()
            
    def lineReceived(self, line):
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
                                            
        if 'FORWARD' in args_str:
            self.work_vars['push_forward'] = True
            args_str.replace("FORWARD ","")
        else:
            self.work_vars['push_forward'] = False

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
            self.work_vars['current_ticket'] = self.factory.get_ticket()        
            d = self.factory.execute_block(execute_cmd,
                self.work_vars['current_ticket'])
            d.addCallback(self.execute_ok_block)
            d.addErrback(self.execute_fail)
        else:                   
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
    ##### The MOVE command
    #####

    def handle_init_MOVE(self, args):
        """Handle a MOVE commmand."""
        
        print "Moving: ", args

        self.work_vars['move_target_addrs'] = []
        self.work_vars['move_failures'] = []            

        # Process args
        args_split = args.split(" ", 2)
        if len(args_split) < 3:
            self.finish_move("FAIL")
        # No test is done to see if these are valid python variable names
        self.work_vars['move_source_key'] = args_split[0]
        self.work_vars['move_target_key'] = args_split[1]
        try:
            self.work_vars['move_targets'] = \
                map(int,args_split[2].split(" "))
        except:
            self.move_finish("FAIL")
        else:
            # Lookup the addresses and fail one any don't exist        
            for t in self.work_vars['move_targets']:
                t_addr = self.factory.get_cluster_addr(t)
                if t_addr is None:
                    self.work_vars['move_failures'].append(t)                    
                self.work_vars['move_target_addrs'].append(t_addr)
            if None in self.work_vars['move_target_addrs']:
                self.move_finish("FAIL")
            else: # All addresses are present in the cluster
                print "Targets: ", self.work_vars['move_targets']
                print "Targets: ", self.work_vars['move_target_addrs']                
                self.work_vars['current_ticket'] = \
                    self.factory.get_ticket()
                d = self.factory.pull(pull_name, 
                    self.work_vars['current_ticket'])                   
                d.addCallback(self.move_pull_ok)
                d.addErrback(self.move_pull_fail)
                 
    def move_pull_ok(self, result):
        # Add error code here and chain the callbacks
        print "move_pull_ok", result
        try:
            self.work_vars['move_pickle'] = pickle.dumps(result, 2)
        except:
            self.move_finish("FAIL")
        else:
            for t in self.work_vars['move_targets']:
                t_addr = self.factory.get_cluster_addr(t)
                c = ClientCreator(reactor, Mover)
                d = c.connectTCP(t_addr[0], t_addr[1])
                d.addCallback(self.move_push)

    def move_pull_fail(self, f):
        print f.getTrackback()
        self.move_finish("FAIL")
                   
    def move_push(self, proto):
        d = proto.push(self.work_vars['move_target_key'], 
            self.work_vars['move_pickle'])
        
        def handle_move_push(result):
            if result:
                self.move_finish("OK")
            else:
                self.move_finish("FAIL")
        d.addCallback(handle_move_push)
    
    def move_push(self):
        pass
           
    def move_finish(self, msg):
        flist = map(str, self.work_vars['move_failures'])
        fstr = " ".join(flist)
        self.sendLine("MOVE %s %s" % (msg, fstr))
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
        
    def handle_init_ALLOW(self, args):
        args_split = args.split(" ")
        if len(args_split) == 2:
            action, host = args_split
            if action == "TRUE":
                self.factory.allow_client(host)
                self.sendLine('ALLOW OK')
            elif action == "FALSE":
                self.factory.deny_client(host)
                self.sendLine('ALLOW OK')
            else:
                self.sendLine('ALLOW FAIL')
        else:
            self.sendLine('ALLOW FAIL')
        
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

    # The CLUSTER command

    def handle_init_CLUSTER(self, args):
        if args == "CLEAR":
            self.factory.clear_cluster()
            self.cluster_finish("OK")
        elif args == "CREATE":
            self.state = 'cluster'
        else:
            self.cluster_finish('FAIL')

    def cluster_finish(self,msg):
        self.sendLine("CLUSTER %s" % msg)
        self._reset()
    
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
   
class KernelFactoryBase:

    def __init__(self, allow=[], notify=[]):
        self._notifiers = notify
        self._allowed_clients = allow
        self._cluster_addrs = []
        
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
            
    # Client validation addresses
            
    def allow_client(self, c):
        if c not in self._allowed_clients:
            self._allowed_clients.append(c)
        #print "Allowed: ", self._allowed_clients
            
    def deny_client(self, c):
        if c in self._allowed_clients:
            del self._allowed_clients[self._allowed_clients.index(c)]
        #print "Allowed: ", self._allowed_clients
            
    def is_allowed(self, c):
        if c in self._allowed_clients or 'all' in self._allowed_clients:
            return True
        else:
            return False
            
    # Cluster addresses
            
    def create_cluster(self, ca_list):
        self._cluster_addrs = ca_list
        for ca in self._cluster_addrs:
            self.allow_client(ca[0]) # Just the ip address
        #print "Cluster: ", self._cluster_addrs

    def clear_cluster(self):
        for ca in self._cluster_addrs:
            self.deny_client(ca[0])
        self._cluster_addrs = []
            
    def cluster_addrs(self):
        return self._cluster_addrs
        
    def get_cluster_addr(self, i):
        try:
            wa = self._cluster_addrs[i]
        except:
            return None
        else:
            return wa
            
    def cluster_count(self):
        return len(self._cluster_addrs)

   
class KernelTCPFactory(protocol.ServerFactory, KernelFactoryBase):
    protocol = KernelTCPProtocol
    
    def __init__(self, allow=[], notify=[], mpi=None, callbackAddr=None):
        self.qic = QueuedInteractiveConsole()
        self.qic.start_work()
        self.callbackAddr = callbackAddr
        self.mpi =  mpi
        if self.mpi:
            self.qic.push('mpi',mpi)
        KernelFactoryBase.__init__(self, allow, notify)

    def stopFactory(self):
        pass
        #if self.mpi:
        #    self.qic.execute('MPI.Finalize()')

    def startFactory(self):
        if self.callbackAddr:
            ccb = callback.CallbackClientFactory(('192.168.0.1',10105),tries=3)
            reactor.connectTCP('127.0.0.1', 12001, ccb)
        
    # Kernel methods
            
    def get_ticket(self):
        return self.qic.get_ticket()
        
    def push(self, key, value, ticket=None):
        self.qic.push(key, value, ticket)
        
    def pull(self, key, ticket):
        d = threads.deferToThread(self.qic.pull, key, ticket)
        return d
        
    def execute(self, source, ticket):
        d = threads.deferToThread(self.qic.execute, source, ticket)
        return d
        
    def execute_block(self, source, ticket):
        result = self.qic.execute(source, ticket, block=True)
        return defer.succeed(result)
        
    def status(self):
        return self.qic.status()
        
    def reset(self):
        self.qic.reset()
        
    def get_result(self, i):
        d = threads.deferToThread(self.qic.get_result, i)
        return d
        
    def get_last_result(self):
        d = threads.deferToThread(self.qic.get_last_result)
        return d
        
class KernelTCPFactoryGUI(protocol.ServerFactory, KernelFactoryBase):
    protocol = KernelTCPProtocol

    def __init__(self, allow=[], notify=[]):
        self.tic = TrappingInteractiveConsole()
        KernelFactoryBase.__init__(self, allow, notify)

    # Kernel methods
            
    def get_ticket(self):
        return 0
        
    def push(self, key, value, ticket=None):
        self.tic.update({key:value})
        
    def pull(self, key, ticket=None):
        value = self.tic.get(key)
        return defer.succeed(value)

    def execute(self, source, ticket=None):
        return self.execute_block(source)
                
    def execute_block(self, source, ticket=None):
        self.tic.runlines(source)
        result = self.tic.get_last_result()
        return defer.succeed(result)
        
    def status(self):
        return 0
        
    def reset(self):
        self.tic.locals = {}
        
    def get_result(self, i):
        return self.tic.get_result(i)
        
    def get_last_result(self):
        return self.tic.get_last_result()
        
class ThreadlessKernelTCPFactory(protocol.ServerFactory, KernelFactoryBase):
    protocol = KernelTCPProtocol
    
    def __init__(self, allow=[], notify=[], mpi=None):
        self.tic = TrappingInteractiveConsole()
        self.mpi =  mpi
        if self.mpi:
            self.qic.push('mpi',mpi)
        KernelFactoryBase.__init__(self, allow, notify)

    def stopFactory(self):
        pass
        #if self.mpi:
        #    self.tic.runlines('MPI.Finalize()')

    # Kernel methods
            
    def get_ticket(self):
        return 0
        
    def push(self, key, value, ticket=None):
        self.tic.update({key:value})
        
    def pull(self, key, ticket):
        data = self.tic.get(key)
        return defer.succeed(data)
        
    def execute(self, source, ticket):
        self.tic.runlines(source)
        result = self.tic.get_last_result()
        return defer.succeed(result)
        
    def execute_block(self, source, ticket):
        return self.execute(source=source, ticket=ticket)
        
    def status(self):
        return 0
        
    def reset(self):
        del self.tic
        self.tic = TrappingInteractiveConsole()
        
    def get_result(self, i):
        result = self.tic.get_result(i)
        return defer.succeed(result)
        
    def get_last_result(self):
        result = self.tic.get_last_result()
        return defer.succeed(result)
        
        
