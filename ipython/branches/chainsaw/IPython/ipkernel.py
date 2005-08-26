import cPickle as pickle

from twisted.internet import protocol, reactor, threads, defer
from twisted.protocols import basic
from twisted.mail.imap4 import LiteralString
from twisted.python import log
import sys

from ipic import QueuedInteractiveConsole

# modified from twisted.mail.imap4.LiteralString
class LiteralString:
    def __init__(self, size, defered):
        self.size = size
        self.data = []
        self.defer = defered

    def write(self, data):
        print "writing", data, len(data), type(data)
        for d in data:
            print d
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
        
class IPythonTCPProtocol(basic.LineReceiver):

    def connectionMade(self):
        log.msg("Connection Made...")
        self.state = 'init'
        self.work_vars = {}
        peer = self.transport.getPeer()
        if not self.factory.is_validated(peer.host):
            log.msg("Invalidated Client: %s" % peer.host)
            self.transport.loseConnection()
            
    def lineReceived(self, line):
        print "Line Received: ", line, self.state
        split_line = line.split(" ", 1)
        if len(split_line) == 1:
            cmd = split_line[0]
            args = None
        elif len(split_line) == 2:
            cmd = split_line[0]
            args = split_line[1]
        print "Command: ", cmd
        print "Arguments: ", args

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
        print "In rawDataReceived"
        passon = self._pendingLiteral.write(data)
        print "passon = ", passon
        if passon is not None:
            self.setLineMode(passon) # should I reset the state here?
        
    def reset_work_vars(self):
        self.work_vars = {}
                
    ##### The PUSH command

    def handle_init_PUSH(self, args):
        print "handle_init_PUSH"
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
        self.state = 'pending'
        self._pendingLiteral = LiteralString(size, d)
        self.setRawMode()
        return d        

    def push_finish(self,msg):
        self.sendLine("PUSH %s" % msg)
        self.state = 'init'
        self.reset_work_vars()
    
    def handle_pushing_PICKLE(self, size_str):
        print "Handling pushing PICKLE", size_str

        try:
            size = int(size_str)
        except (ValueError, TypeError):
            self.push_finish("FAIL")
        else:
            d = self.setup_literal(size)
        
            def process_pickle(package):
                try:
                    data = pickle.loads(package)
                except pickle.PickleError:
                    self.push_finish("FAIL")
                else:
                    print "Received data: ", data
                    # What if this fails?
                    self.factory.push(self.work_vars['push_name'],
                        data, self.work_vars['current_ticket'])
                     
                    self.push_finish("OK")
       
            d.addCallback(process_pickle)

    ##### The PULL command

    def handle_init_PULL(self, args):
        print "handle_init_PULL"
        if args:
            split_args = args.split(" ")
            pull_name = split_args[0]
            if pull_name == "COMMAND":
                # Handle an STDOUT request
                self.sendLine("COMMAND stdout")
                self.transport.write("pickled tuple")
                self.sendLine("PULL OK")
            else:
                # All other pull request are from the kernel's namespace
                self.work_vars['current_ticket'] = self.factory.get_ticket()
                d = self.factory.pull(pull_name, 
                    self.work_vars['current_ticket'])

                def pull_ok(result):
                    # Add error code here and chain the callbacks
                    presult = pickle.dumps(result, 2)
                    self.sendLine("PICKLE %s" % len(presult))
                    self.transport.write(presult)
                    self.sendLine("PULL OK")
                                        
                def pull_fail(failure):
                    self.sendLine("PULL FAIL")
                    
                d.addCallback(pull_ok)
                d.addErrback(pull_fail)
        else:
            self.write('PULL FAIL')
            
        self.state = 'init'            
        self.reset_work_vars()

    ##### The EXECUTE command

    def handle_init_EXECUTE(self, args):
        print "Handling EXECUTE", args
        
        arg_list = args.split(" ",1)
        
        # See if we should print the stdout of this command
        if arg_list[0] == 'PRINT':
            execute_print = True
            if len(arg_list) == 2:
                execute_cmd = arg_list[1]
            else:
                self.sendLine("EXECUTE FAIL")
                return
        else:
            print_stdout = False
            execute_cmd = args

        self.work_vars['current_ticket'] = self.factory.get_ticket()   
        d = self.factory.execute(execute_cmd, 
            self.work_vars['current_ticket'])
        # Return Ok after the command is queued
        self.sendLine('EXECUTE OK')
        
        # These callbacks are used to return stdout and stderr
        # on a different channel.
        def execute_ok(result):
            for tonotify in self.factory.notifiers():
                print "Notifying: ", tonotify
                reactor.listenUDP(0,
                    CommandReporter(result[0], result[1], tonotify) )    
        def execute_fail(failure):
            pass
        d.addCallback(execute_ok)
        d.addErrback(execute_fail)
        
        self.state = 'init'
        self.reset_work_vars()
    
    ##### Kernel control commands
    
    def handle_init_STATUS(self, args):
        print "Handling STATUS", args
        status = self.factory.status()
        self.sendLine('STATUS OK %s %s' % (status, self.state))
        
    def handle_init_VALIDATE(self, args):
        print "Handling VALIDATE"
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
        print "Handling NOTIFY"
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

    
    def handle_RESET(self, args):
        print "Handling RESET", args
        self.factory.reset()
        self.sendLine('RESET OK')
        self.state = 'init'
        self.reset_work_vars()
        
    def handle_KILL(self, args):
        print "Handling KILL", args
        self.sendLine('KILL OK')
        reactor.stop()
        
    def handle_DISCONNECT(self,args):
        print "Handling DISCONNECT"
        self.transport.loseConnection()
    
   
class IPythonTCPFactory(protocol.ServerFactory):
    protocol = IPythonTCPProtocol
    
    def __init__(self, validate=[], notify=[]):
        self.qic = QueuedInteractiveConsole()
        self.qic.start_work()
        self._notifiers = notify
        self._validated_clients = validate
        
    def notifiers(self):
        return self._notifiers
        
    def add_notifier(self, n):
        if n not in self._notifiers:
            self._notifiers.append(n)
        print self._notifiers
            
    def del_notifier(self, n):
        if n in self._notifiers:
            del self._notifiers[self._notifiers.index(n)]
        print self._notifiers
            
    def validate_client(self, c):
        if c not in self._validated_clients:
            self._validated_clients.append(c)
            
    def invalidate_client(self, c):
        if c in self._validated_clients:
            del self._validated_clients[self._validated_clients.index(c)]
            
    def is_validated(self, c):
        if c in self._validated_clients:
            return True
        else:
            return False
            
    def get_ticket(self):
        return self.qic.get_ticket()
        
    def push(self, key, value, ticket=None):
        print "Pushing into the namespace"
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
        
log.startLogging(sys.stdout)
        
reactor.listenTCP(10104, IPythonTCPFactory(validate=['127.0.0.1']))
reactor.run()