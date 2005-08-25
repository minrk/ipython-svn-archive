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

class IPythonTCPProtocol(basic.LineReceiver):

    def connectionMade(self):
        log.msg("Connection Made...")
        self.state = 'init'
        self.work_vars = {}
        
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
            pass     
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
        self.sendLine('STATUS OK %s' % status)
        
    def handle_init_VALIDATEIP(self, args):
        print "Handling VALIDATE"
        self.sendLine('VALIDATEIP OK')
        
    def handle_init_NOTIFYIP(self, args):
        print "Handling NOTIFY"
        self.sendLine('NOTIFYIP OK')    
    
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
    
    def __init__(self):
        self.qic = QueuedInteractiveConsole()
        self.qic.start_work()
        
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
        
reactor.listenTCP(10104, IPythonTCPFactory())
reactor.run()