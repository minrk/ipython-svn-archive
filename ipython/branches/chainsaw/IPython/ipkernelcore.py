import cPickle as pickle

from twisted.internet import protocol, reactor, threads, defer
from twisted.protocols import basic
from twisted.python.runtime import seconds
from twisted.python import log
from twisted.python import failure
import sys

from ipic import QueuedInteractiveConsole

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

class CommandReporter(protocol.DatagramProtocol):

    def __init__(self, cmd_num, cmd_tuple, addr):
        self.cmd_num = cmd_num
        self.cmd_tuple = cmd_tuple
        self.addr = addr
        
    def startProtocol(self):
        print "Protocol running: ", self.cmd_num, self.cmd_tuple, self.addr
        package = pickle.dumps(self.cmd_tuple,2)
        self.transport.write("COMMAND %i %s" % (self.cmd_num, package), 
            self.addr)
        self.tried = True
        
    def datagramReceived(self,data, sending_addr):
        print "Datagram Received: ", data, sending_addr
        if sending_addr == self.addr and data == "COMMAND OK":
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
            
class IPythonTCPProtocol(basic.LineReceiver):

    def connectionMade(self):
        log.msg("Connection Made...")
        #self.transport.setTcpNoDelay(True)
        self.state = 'init'
        self.work_vars = {}
        peer = self.transport.getPeer()
        if not self.factory.is_validated(peer.host):
            log.msg("Invalidated Client: %s" % peer.host)
            self.transport.loseConnection()
            
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
        if args:
            split_args = args.split(" ")
            self.work_vars['push_name'] = split_args[0]
            if 'FORWARD' in split_args:
                self.work_vars['push_forward'] = True
            else:
                self.work_vars['push_forward'] = False
            self.state = 'pushing'
            self.work_vars['current_ticket'] = self.factory.get_ticket()
        else:
            self.push_finish('FAIL')

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
        if args:
            split_args = args.split(" ")
            pull_name = split_args[0]
            if pull_name == "COMMAND":
                # Handle an STDOUT request
                self.sendLine("COMMAND stdout")
                self.transport.write("pickled tuple")
                self.pull_finish("OK")
            else:
                # All other pull request are from the kernel's namespace
                self.work_vars['current_ticket'] = self.factory.get_ticket()
                d = self.factory.pull(pull_name, 
                    self.work_vars['current_ticket'])                   
                d.addCallback(self.pull_ok)
                d.addErrback(self.pull_fail)
        else:
            self.pull_finish("FAIL")
     
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
    ##### The EXECUTE command
    #####
    
    def handle_init_EXECUTE(self, args):
        """Handle the EXECUTE command."""
                
        execute_cmd = args
        self.work_vars['current_ticket'] = self.factory.get_ticket()
        # The deferToThread in this call costs 2 ms currently :(
        d = self.factory.execute(execute_cmd, 
            self.work_vars['current_ticket'])
        self.sendLine('EXECUTE OK')   
        self._reset()
        d.addCallback(self.execute_ok)
        d.addErrback(self.execute_fail)
        
    def execute_ok(self, result):
        for tonotify in self.factory.notifiers():
            reactor.listenUDP(0,CommandReporter(result[0], 
                result[1], tonotify) )
                
    def execute_fail(self, f):
        pass
        
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
        self.sendLine('STATUS OK %s %s' % (status, self.state))
        
    def handle_init_VALIDATE(self, args):
        args_split = args.split(" ")
        if len(args_split) == 2:
            action, host = args_split
            if action == "TRUE":
                self.factory.validate_client(host)
                self.sendLine('VALIDATE OK')
            elif action == "FALSE":
                self.factory.invalidate_client(host)
                self.sendLine('VALIDATE OK')
            else:
                self.sendLine('VALIDATE FAIL')
        else:
            self.sendLine('VALIDATE FAIL')
        
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
    
   
class IPythonTCPFactory(protocol.ServerFactory):
    protocol = IPythonTCPProtocol
    
    def __init__(self, validate=[], notify=[]):
        self.qic = QueuedInteractiveConsole()
        self.qic.start_work()
        self._notifiers = notify
        self._validated_clients = validate
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
            
    def validate_client(self, c):
        if c not in self._validated_clients:
            self._validated_clients.append(c)
        print "Validated: ", self._validated_clients
            
    def invalidate_client(self, c):
        if c in self._validated_clients:
            del self._validated_clients[self._validated_clients.index(c)]
        print "Validated: ", self._validated_clients
            
    def is_validated(self, c):
        if c in self._validated_clients:
            return True
        else:
            return False
            
    # Cluster addresses
            
    def create_cluster(self, ca_list):
        self._cluster_addrs = ca_list
        for ca in self._cluster_addrs:
            self.validate_client(ca[0]) # Just the ip address
        print "Cluster: ", self._cluster_addrs

    def clear_cluster(self):
        for ca in self._cluster_addrs:
            self.invalidate_client(ca[0])
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
        
    def status(self):
        return self.qic.status()
        
    def reset(self):
        self.qic.reset()
        
def main(port):
    log.startLogging(sys.stdout)
        
    reactor.suggestThreadPoolSize(5)
        
    d = reactor.listenTCP(port, IPythonTCPFactory(validate=['127.0.0.1']))
    reactor.run()
    
if __name__ == "__main__":
    port = int(sys.argv[1])
    main(port)