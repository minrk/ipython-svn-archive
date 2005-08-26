import socket
import threading
import pickle

from twisted.internet import reactor, protocol
from twisted.protocols import basic

from IPython.ColorANSI import *

class IPythonTCPClientProtocol(basic.Int32StringReceiver):
    pass

class IPythonTCPClientFactory(protocol.ClientFactory):
    pass
    
class CommandGatherer(object):
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
            if msg_split[0] == "COMMAND" and len(msg_split) == 3:
                try:
                    cmd_num = int(msg_split[1])
                except  (ValueError, TypeError):
                    fail = True
                else:
                    try:
                        cmd_tuple = pickle.loads(msg_split[2])
                    except pickle.PickleError:
                        fail = True
                    else:
                        fail = False
                        print "\n%s[%s]%s In [%i]:%s %s" % \
                            (green, client_addr[0],
                            blue, cmd_num, normal, cmd_tuple[0])
                        if cmd_tuple[1]:
                            print "%s[%s]%s Out[%i]:%s %s" % \
                                (green, client_addr[0],
                                red, cmd_num, normal, cmd_tuple[1])
                        if cmd_tuple[2]:
                            print "%s[%s]%s Err[%i]:\n%s %s" % \
                                (green, client_addr[0],
                                red, cmd_num, normal, cmd_tuple[2])
            else:
                fail = True
                
            if fail:
                s.sendto("COMMAND FAIL", client_addr)
            else:
                s.sendto("COMMAND OK", client_addr)
                
