"""Classes for gathering results from kernels.

IPython kernels send back results (stdout, stderr) to a UDP port.  The classes
in this module listen on the UDP port and hadle the incoming results.

Once the result gatherer has been started you can tell kernels to send results
to the gatherer by using the .notify method of the RemoteKernel or 
InteractiveCluster classes.  Multiple kernels can notify a single gatherer.
"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************
import socket
import threading
import pickle
import time, os

from IPython.ColorANSI import *

from twisted.protocols.basic import LineReceiver
    
class UDPResultGatherer(object):
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
        """Initialize the gatherer on addr = (interface,port)."""
        
        self.addr = addr
        self.hault_lock = threading.Lock()
        
    def start(self, daemonize=True):
        """Start gathering output and errors on the UPD port."""
        t = threading.Thread(target=self._gather, name="Gatherer",
            args=(self.addr,))
        if daemonize:
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
                        (id, cmd_tuple) = pickle.loads(msg_split[2])
                    except pickle.PickleError:
                        fail = True
                    else:
                        fail = False
                        cmd_num = cmd_tuple[0]
                        cmd_stdin = cmd_tuple[1]
                        cmd_stdout = cmd_tuple[2]
                        cmd_stderr = cmd_tuple[3]
                        print "\n%s[%s]:[%i]%s In [%i]:%s %s" % \
                            (green, client_addr[0], id,
                            blue, cmd_num, normal, cmd_stdin)
                        if cmd_stdout:
                            print "%s[%s]:[%i]%s Out[%i]:%s %s" % \
                                (green, client_addr[0], id,
                                red, cmd_num, normal, cmd_stdout)
                        if cmd_stderr:
                            print "%s[%s]:[%i]%s Err[%i]:\n%s %s" % \
                                (green, client_addr[0], id,
                                red, cmd_num, normal, cmd_stderr)
            else:
                fail = True
                
            if fail:
                s.sendto("RESULT FAIL", client_addr)
            else:
                s.sendto("RESULT OK", client_addr)
    

class TCPResultsProtocol(LineReceiver):
    
    blue = TermColors.Blue
    normal = TermColors.Normal
    red = TermColors.Red
    green = TermColors.Green
    
    def connectionMade(self):
        self.peer = self.transport.getPeer()

    def lineReceived(self, line):
        
        msg_split = line.split(" ", 2)
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
                    id = cmd_tuple[0]
                    cmd_num = cmd_tuple[1]
                    cmd_stdin = cmd_tuple[2]
                    cmd_stdout = cmd_tuple[3]
                    cmd_stderr = cmd_tuple[4]
                    print "\n%s[%s]:[%i]%s In [%i]:%s %s" % \
                        (self.green, self.peer.host, id,
                        self.blue, cmd_num, self.normal, cmd_stdin)
                    if cmd_stdout:
                        print "%s[%s]:[%i]%s Out[%i]:%s %s" % \
                            (self.green, self.peer.host, id,
                            self.red, cmd_num, self.normal, cmd_stdout)
                    if cmd_stderr:
                        print "%s[%s]:[%i]%s Err[%i]:\n%s %s" % \
                            (self.green, self.peer.host, id,
                            self.red, cmd_num, self.normal, cmd_stderr)
        else:
            fail = True
            
        if fail:
            self.sendLine("RESULT FAIL")
        else:
            self.sendLine("RESULT OK")
        
    