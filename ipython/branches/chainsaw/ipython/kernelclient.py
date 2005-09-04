import socket
import threading
import pickle
import time
from twisted.internet import reactor, protocol
from twisted.protocols import basic

from IPython.ColorANSI import *

from esocket import LineSocket

class IPythonTCPClientProtocol(basic.Int32StringReceiver):
    pass

class IPythonTCPClientFactory(protocol.ClientFactory):
    pass
    
class ResultGatherer(object):
    """This class listens on a UDP port for kernels reporting stdout and stderr.
    
    The current implementation simply prints the stdin, stdout and stderr
    of each kernel command to standard out in colorized form.
    
    The IPython.ColorANSI module is used to colorize the output.
    
    Currently I use diconnected UDP.  There could be a benefit in going over
    to connected mode.
    
    Also, currently, I don't report the port that the kernel is listening on.
    This information will be useful when multiple kernel's are running on
    a single interface. 
    """
    
    def __init__(self, addr):
        """Initialize the Gatherer on addr = (interface,port)."""
        
        self.addr = addr
        self.hault_lock = threading.Lock()
        
    def start(self):
        """Start gathering output and errors on the UPD port."""
        t = threading.Thread(target=self._gather, name="Gatherer",
            args=(self.addr,))
        t.setDaemon(1)
        self.hault = False
        self.t = t
        t.start()

    def stop(self):
        """Stop gathering output and errors on the UDP port.
        
        Currently this method does not stop the Gatherer thread
        immediately.  Rather it takes _one_ more request.  If there
        are no more requests, then it will hang.
        """
        self.hault_lock.acquire()
        self.hault = True
        self.hault_lock.release()

    def _gather(self, addr):
        """This does the work in the second thread."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(addr)
        blue = TermColors.Blue
        normal = TermColors.Normal
        red = TermColors.Red
        green = TermColors.Green
        while True:
        
            # See if we should stop the thread
            self.hault_lock.acquire()
            hault = self.hault
            self.hault_lock.release()
            if hault:
                break 

            # Get and print a message
            message, client_addr = s.recvfrom(8192)
            msg_split = message.split(" ", 2)
            if msg_split[0] == "RESULT" and len(msg_split) == 3:
                try:
                    nbytes = int(msg_split[1])
                except  (ValueError, TypeError):
                    fail = True
                else:
                    try:
                        cmd_tuple = pickle.loads(msg_split[2])
                    except pickle.PickleError:
                        fail = True
                    else:
                        fail = False
                        cmd_num = cmd_tuple[0]
                        cmd_stdin = cmd_tuple[1]
                        cmd_stdout = cmd_tuple[2]
                        cmd_stderr = cmd_tuple[3]
                        print "\n%s[%s]%s In [%i]:%s %s" % \
                            (green, client_addr[0],
                            blue, cmd_num, normal, cmd_stdin)
                        if cmd_stdout:
                            print "%s[%s]%s Out[%i]:%s %s" % \
                                (green, client_addr[0],
                                red, cmd_num, normal, cmd_stdout)
                        if cmd_stderr:
                            print "%s[%s]%s Err[%i]:\n%s %s" % \
                                (green, client_addr[0],
                                red, cmd_num, normal, cmd_stderr)
            else:
                fail = True
                
            if fail:
                s.sendto("RESULT FAIL", client_addr)
            else:
                s.sendto("RESULT OK", client_addr)
                
class RemoteKernel(object):
    
    def __init__(self, addr):
        self.addr = addr
        self.extra = ''
        
    def is_connected(self):
        if hasattr(self, 's'):
            try:
                self.fd = self.s.fileno()
            except socket.error:
                return False
            else:
                return True
                
    def _check_connection(self):
        if not self.is_connected():
            self.connect()
            
    def connect(self):
        print "Connecting to kernel: ", self.addr
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error, e:
            print "Strange error creating socket: %s" % e
            
        try:
            self.s.connect(self.addr)
        except socket.gaierror, e:
            print "Address related error connecting to sever: %s" % e
        except socket.error, e:
            print "Connection error: %s" % e
                
        self.es = LineSocket(self.s)
        # Turn of Nagle's algorithm to prevent the 200 ms delay :)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY,1)
        
    def execute(self, source, block=False):
        self._check_connection()
        if block:
            self.es.write_line("EXECUTE BLOCK %s" % source)
            line, self.extra = self.es.read_line(self.extra)
            line_split = line.split(" ")
            if line_split[0] == "RESULT" and len(line_split) == 2:
                try:
                    nbytes = int(line_split[1])
                except:
                    print "Server did not return the length of data."
                    return False
                package, self.extra = self.es.read_bytes(nbytes, self.extra)
                data = pickle.loads(package)
                line, self.extra = self.es.read_line(self.extra)
            else:
                data = None
                line = ""
        else:
            self.es.write_line("EXECUTE %s" % source)
            line, self.extra = self.es.read_line(self.extra)
            data = None
            
        if line == "EXECUTE OK":
            return data
        else:
            return False
        
    def push(self, value, key, forward=False):
        self._check_connection()
        try:
            package = pickle.dumps(value, 2)
        except picket.PickleError, e:
            print "Object cannot be pickled: ", e
            return False
        if forward:
            self.es.write_line("PUSH FORWARD %s" % key)
        else:
            self.es.write_line("PUSH %s" % key )
        self.es.write_line("PICKLE %i" % len(package))
        self.es.write_bytes(package)
        line, self.extra = self.es.read_line(self.extra)
        if line == "PUSH OK":
            return True
        if line == "PUSH FAIL":
            return False
        
    def __setitem__(self, key, value):
        self.push(value, key)
        
    def pull(self, key):
        self._check_connection()    
    
        self.es.write_line("PULL %s" % key)
        line, self.extra = self.es.read_line(self.extra)
        line_split = line.split(" ", 1)
        if line_split[0] == "PICKLE":
            try:
                nbytes = int(line_split[1])
            except (ValueError, TypeError):
                raise
            else:
                package, self.extra = self.es.read_bytes(nbytes, self.extra)
                line, self.extra = self.es.read_line(self.extra)
                try:
                    data = pickle.loads(package)
                except pickle.PickleError, e:
                    print "Error unpickling object: ", e
                    return None
                else:
                    if line == "PULL OK":
                        return data
                    else:
                        return None
        else:
            # For other data types
            pass

    def __getitem__(self, key):
        return self.pull(key)

    def result(self, number=None):
        self._check_connection()    
    
        if number is None:
            self.es.write_line("PULL RESULT")
        else:
            self.es.write_line("PULL RESULT %i" % number)
        line, self.extra = self.es.read_line(self.extra)
        line_split = line.split(" ", 1)
        if line_split[0] == "RESULT":
            try:
                nbytes = int(line_split[1])
            except (ValueError, TypeError):
                raise
            else:
                package, self.extra = self.es.read_bytes(nbytes, self.extra)
                line, self.extra = self.es.read_line(self.extra)
                try:
                    data = pickle.loads(package)
                except pickle.PickleError, e:
                    print "Error unpickling object: ", e
                    return None
                else:
                    if line == "PULL OK":
                        return data
                    else:
                        return None
        else:
            # For other data types
            return False
        
    def move(keya, keyb, target):
        self._check_connection()
        print "Mpve is not implemented yet."
        #write_line("MOVE %s %s %" % (keya, keyb, target))
        #read_line()

    def status(self):
        self._check_connection()

        self.es.write_line("STATUS")
        line, self.extra = self.es.read_line(self.extra)
        line_split = line.split(" ")
        if len(line_split) == 4:
            if line_split[0] == "STATUS" and line_split[1] == "OK":
                return (int(line_split[2]), line_split[3])
            else:
                return None
        else:
            return None

    def validate(self, ip, flag=True):
        self._check_connection()
        
        if flag:
            self.es.write_line("VALIDATE TRUE %s" % ip)
        else:
            self.es.write_line("VALIDATE FALSE %s" % ip)
        line, self.extra = self.es.read_line(self.extra)
        if line == "VALIDATE OK":
            return True
        else:
            return False      

    def notify(self, addr, flag=True):
        self._check_connection()
        
        host, port = addr
        if flag:
            self.es.write_line("NOTIFY TRUE %s %s" % (host, port))
        else:
            self.es.write_line("NOTIFY FALSE %s %s" % (host, port))
        line, self.extra = self.es.read_line(self.extra)
        if line == "NOTIFY OK":
            return True
        else:
            return False        
       
    def cluster(self, addrs=None):
        self._check_connection()
        if addrs is None:
            self.es.write_line("CLUSTER CLEAR")
            line, self.extra = self.es.read_line(self.extra)
            if line == "CLUSTER OK":
                return True
            if line == "CLUSTER FAIL":
                return False
        else:
            try:
                package = pickle.dumps(addrs, 2)
            except picket.PickleError, e:
                print "Pass a valid python list of addresses: ", e
                return False
            else:
                self.es.write_line("CLUSTER CREATE")
                self.es.write_line("PICKLE %i" % len(package))
                self.es.write_bytes(package)
                line, self.extra = self.es.read_line(self.extra)
                if line == "CLUSTER OK":
                    return True
                if line == "CLUSTER FAIL":
                    return False

    def reset(self):
        self._check_connection()
            
        self.es.write_line("RESET")
        line, self.extra = self.es.read_line(self.extra)
        if line == "RESET OK":
            return True
        else:
            return False      
                           
    def kill(self):
        self._check_connection()    
    
        self.es.write_line("KILL")
        self.s.close()
        del self.s
        del self.es
        return True   

    def disconnect(self):
        if self.is_connected():
            self.es.write_line("DISCONNECT")
            line, self.extra = self.es.read_line(self.extra)
            if line == "DISCONNECT OK":
                self.s.close()
                del self.s
                del self.es
                return True
            else:
                return False
        else:
            return True
            
class InteractiveCluster(object):
    
    def __init__(self):
        self.count = 0
        self.workers = []
        self.worker_addrs = []
        
    def start(self, addr_list):
        for a in addr_list:
            self.worker_addrs.append(a)
            self.workers.append(RemoteKernel(a))
        self.count = len(self.workers)
        
        # Let everyone know about each other
        for w in self.workers:
            w.cluster(self.worker_addrs)
            
        return True
        
    def __getitem__(self, key):
        if isinstance(key, int):
            return self.workers[key]
        elif isinstance(key, str):
            return self.pull(key)
            
    def __len__(self):
        return selr.count
        
    def stop(self):
        for w in workers:
            w.kill()
            
    def push(self, value, key, workers=None):
        if workers is None:
            for w in self.workers:
                w.push(value, key)
        else:
            for w_num in workers:
                self.workers[w_num].push(value, key)
                
    def __setitem__(self, key, value):
        self.push(value, key)
        
    def pull(self, key, workers=None):
        results = []
        if workers is None:
            for w in self.workers:
                results.append(w.pull(key))
        else:
            for w_num in workers:
                results.append(self.workers[w_num].pull(key))
        return results
                
    def execute(self, source, workers=None):
        if workers is None:
            for w in self.workers:
                w.execute(source)
        else:
            for w_num in workers:
                self.workers[w_num].execute(source)
            
    def notify(self, addr):
        for w in self.workers:
            w.notify(addr)
            
    def reset(self):
        for w in self.workers:
            w.reset()
            
    
                  