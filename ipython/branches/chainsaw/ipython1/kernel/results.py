"""Classes for gathering results from kernels.

This module introduces the notion of a Notifier, which is the mchanism a 
Controller uses for upward communication with clients.

it consists of a Parent and a Child, where the parent notifies its children
The ControllerService is a NotifierParent, and a Results Gatherer is a Child.
An object can implement INotifierParent and INotifierChild, as the notify
method is meant to behave the same.

Parents maintain a list of children in a dict {child.key: child,...}
"""
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import types, cPickle as pickle

from zope.interface import Interface, implements, interface
from twisted.protocols.basic import LineReceiver
from twisted.internet import protocol, reactor, defer
from twisted.python import components, log

from IPython.ColorANSI import TermColors

#-------------------------------------------------------------------------------
# The Parent 
#-------------------------------------------------------------------------------

class INotifierParent(Interface):
    """The interface for a NotifierParent object."""
    
    notifiers = interface.Attribute("The dict of notifier objects")
    
    def addNotifier(notifier):
        """Adds a notifier to the set of children to notify.
        
        Notifier must implement INotifierChild
        """
    
    def delNotifier(key):
        """Removes a notifier from the set of children to notify by key."""
    
    def notify(result):
        """Notifies children of result.  
        
        Result must be a tuple of the form: 
            (node_id, cmd_num, stdin, stdout, stderr)
        """

class NotifierParent(object):
    """An object that notifies children of results."""
    
    implements(INotifierParent)
    _notifiers = {}
    
    # notification methods 
    
    notifiers = property(lambda self: self._notifiers, lambda self,_: 
            "don't explicitly write to my notifier!") 
    
    def addNotifier(self, n):
        if n.key not in self._notifiers:
            self._notifiers[n.key] = n
            n.notifyOnDisconnect(self.delNotifier,n.key)
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
        for tonotify in self.notifiers.values():
            tonotify.notify(result)
        return result
    
#-------------------------------------------------------------------------------
# The Child 
#-------------------------------------------------------------------------------

class INotifierChild(Interface):
    """An interface for notifier objects."""
    
    key = interface.Attribute("The key for registration")
    
    def notify(result):
        """Handle a result tuple (id, cmd_num, in, out, err)."""
    
    def notifyOnDisconnect(f, *a, **kw):
        """Function to be called on disconnect."""
    
class BaseNotifierChild(object):
    """A base class for building NotifierChildren.  
    
    It provides a generic implementation of notifyOnDisconnect, and sets key 
    to None, which means it is unhashable, so NotifierChildren should define 
    self.key in a unique way.
    """

    implements(INotifierChild)
    _disconnectNotifiers = []
    key = None
    
    def notifyOnDisconnect(self, f, *a, **kw):
        assert callable(f), "f must be callable"
        self._disconnectNotifiers.append((f, a, kw))
    
    def onDisconnect(self, *args, **kwargs):
        for f,a,kw in self._disconnectNotifiers:
            try:
                f(*a, **kw)
            except:
                self._disconnectNotifiers.remove((f,a,kw))
    

def notifierFromFunction(f):
    """An adapter for building a basic notifier Child from a function.
    
    The function itself will be called as notify.  
    
    It is assumed that the function will never 'disconnect'.
    """

    n = BaseNotifierChild()
    n.key = repr(f)
    n.notify = f
    return n

components.registerAdapter(notifierFromFunction,
        types.FunctionType, INotifierChild)


#-----------------------------------------------------------------------------
# TCP Results Gatherer specific Objects
#-----------------------------------------------------------------------------

class TCPNotifierChild(BaseNotifierChild):
    """The Child class for the TCPResultsGatherer in ControllerService."""
    
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
    """A small client factory and protocol for TCPResultsGatherer."""
    
    protocol = LineReceiver
    protocol.lineReceived = lambda _,__: None
    def __init__(self, onDisconnect=None):
        if callable(onDisconnect):
            self.clientConnectionLost = self.clientConnectionFailed = onDisconnect

class TCPResultsProtocol(LineReceiver):
    """The protocol used for TCP notifications."""
    
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
    



    
