"""Classes for gathering results from kernels.

IPython kernels send back results (stdout, stderr) to a UDP port.  The classes
in this module listen on the UDP port and hadle the incoming results.

Once the result gatherer has been started you can tell kernels to send results
to the gatherer by using the .notify method of the RemoteKernel or 
InteractiveCluster classes.  Multiple kernels can notify a single gatherer.
"""

#*****************************************************************************
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import socket, threading, types, cPickle as pickle

from zope.interface import Interface, implements, interface
from twisted.protocols.basic import LineReceiver
from twisted.internet import protocol, reactor, defer
from twisted.python import components, log

from IPython.ColorANSI import *

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
    


class UDPResultGatherer(object):
    """
    The UDP result system is currently broken!
    
    This class listens on a UDP port for kernels reporting stdout and stderr.
    
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
            msg_split = message.split(" ", 1)
            if msg_split[0] == "RESULT" and len(msg_split) == 2:
                try:
                    (id, cmd_tuple) = pickle.loads(msg_split[1])
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
        print "Connected Controller: %s" %(self.peer.host)
    
    def connectionLost(self, reason):
        print "Disconnected Controller: %s" %(self.peer.host)
    
    def lineReceived(self, line):
        
        msg_split = line.split(" ", 1)
        if msg_split[0] == "RESULT" and len(msg_split) == 2:
            try:
                cmd_tuple = pickle.loads(msg_split[1])
            except pickle.PickleError:
                fail = True
            else:
                fail = False
                id = cmd_tuple[0]
                cmd_num = cmd_tuple[1]
                cmd_stdin = cmd_tuple[2]
                cmd_stdout = cmd_tuple[3]
                cmd_stderr = cmd_tuple[4]
                print "\n%s[%s:%i]%s In [%i]:%s %s" % \
                    (self.green, self.peer.host, id,
                    self.blue, cmd_num, self.normal, cmd_stdin)
                if cmd_stdout:
                    print "%s[%s:%i]%s Out[%i]:%s %s" % \
                        (self.green, self.peer.host, id,
                        self.red, cmd_num, self.normal, cmd_stdout)
                if cmd_stderr:
                    print "%s[%s:%i]%s Err[%i]:\n%s %s" % \
                        (self.green, self.peer.host, id,
                        self.red, cmd_num, self.normal, cmd_stderr)
        else:
            fail = True
            
        if fail:
            self.sendLine("RESULT FAIL")
        else:
            self.sendLine("RESULT OK")
    


# Notifier - the Controller side of the results objects
class NotifierParent(object):
    _notifiers = {}
    # notification methods 
        
    def notifiers(self):
        return self._notifiers
    
    def addNotifier(self, n):
        if n.key not in self._notifiers:
            self._notifiers[n.key] = n
            print n.notifyOnDisconnect(self.delNotifier,n.key)
            log.msg("Notifiers: %s" % self._notifiers)
        return defer.succeed(None)
    
    def delNotifier(self, key):
        if key in self._notifiers:
            try:
                del self._notifiers[key]
            except KeyError:
                pass
            log.msg("Notifiers: %s" % self._notifiers)
        return defer.succeed(None)
    
    def notify(self, result):
        for tonotify in self.notifiers().values():
            tonotify.notify(result)
        return result
    

class INotifierChild(Interface):
    """an interface for notifier objects"""
    
    key = interface.Attribute("The key for registration")
    
    def notify(result):
        """notify of a result Tuple"""
    
    def notifyOnDisconnect(f, *a, **kw):
        """function to be called on disconnect"""
    


class BaseNotifierChild(object):
    implements(INotifierChild)
    _disconnectNotifiers = []
    
    def notifyOnDisconnect(self, f, *a, **kw):
        if not callable(f):
            return False
        else:
            self._disconnectNotifiers.append((f, a, kw))
    
    def onDisconnect(self, *args, **kwargs):
        for f,a,kw in self._disconnectNotifiers:
            try:
                f(*a, **kw)
            except:
                self._disconnectNotifiers.remove((f,a,kw))
    

def notifierFromFunction(f):
    n = BaseNotifierChild()
    n.key = repr(f)
    n.notify = f
    return n

components.registerAdapter(notifierFromFunction,
        types.FunctionType, INotifierChild)

class TCPNotifierChild(BaseNotifierChild):
    
    def __init__(self, addr):
        self.key = addr
        self.host = addr[0]
        self.port = addr[1]
        self.factory = NotifierChildFactory(self.onDisconnect)
        self.client = reactor.connectTCP(self.host, self.port, self.factory)
    
    def notify(self, result):
        package = pickle.dumps(result, 2)
        if self.client.transport.protocol is not None:
            self.client.transport.protocol.sendLine("RESULT %s" %package)
    

components.registerAdapter(TCPNotifierChild, tuple, INotifierChild)

class NotifierChildFactory(protocol.ClientFactory):
    """A small client factory and protocol for the tcp results gatherer"""
    protocol = LineReceiver
    protocol.lineReceived = lambda _,__: None
    def __init__(self, onDisconnect=None):
        if callable(onDisconnect):
            self.clientConnectionLost = self.clientConnectionFailed = onDisconnect
    
