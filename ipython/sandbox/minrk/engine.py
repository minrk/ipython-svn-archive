"""protocol and factory adapted from kernel1p.kernelcore for ipengine"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************
import cPickle as pickle
import sys

from twisted.internet import protocol, reactor, threads, defer
from twisted.protocols import basic
from twisted.python.runtime import seconds
from twisted.python import log
from twisted.python import failure
from zope.interface import implements

from ipython1.kernel import networkinterfaces as NI

class EngineProtocol(basic.Int32StringReceiver):
    implements(NI.IEngineProtocol)
    
    def connectionMade(self):
        log.msg("Connection Made...")
        self.transport.setTcpNoDelay(True)
        peer = self.transport.getPeer()
        if not self.factory.is_allowed(peer.host):
            log.msg("Denied Client: %s" % peer.host)
            self.transport.loseConnection()
    
    def stringReceived(self, string):
        split_string = string.split(" ", 1)
        if len(split_string) == 1:
            cmd = split_string[0]
            args = None
        elif len(split_string) == 2:
            cmd = split_string[0]
            args = split_string[1]
            
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
                    f(string)
                else:
                    # No handler resolved
                    self.sendString("FAIL")
    
    def _reset(self):
        self.work_vars = {}
        self.state = 'init'
    
    #####   
    ##### The put command
    #####
    
    def handle_put(self, args):
        
        # Parse the args
        if not args:
            self.put_finish("FAIL")
            return
        else:
            try: 
                (key, value) = args.split(' ')
                self.service.put(key,value)
            except:
                self.put_finish("FAIL")
                return
                
            self.put_finish("OK")
    
    def put_finish(self,msg):
        self.sendString("PUT %s" % msg)
        self._reset()
    
    def handle_put_pickle(self, string):
        package = pickle.dumps(string, 2)
        try:
            self.service.put_pickle(package)
        except pickle.PickleError:
            self.put_finish("FAIL")
            return
        
        self.put_finish("OK")
    
    #####
    ##### The get command
    #####
    
    def handle_get(self, args):
        
        # Parse the args
        if not args:
            self.get_finish("FAIL")
            return
        else:
            try:
                package = self.service.get_pickle(args)
            except:
                self.get_finish("FAIL")
                return
            
            self.get_finish("OK PICKLE %s" % package)
    
    def get_finish(self, msg):
        self.sendString("GET %s" % msg)
        self._reset()
    
    #####
    ##### The execute command
    #####
    
    def handle_execute(self, args):
        """Handle the execute command."""
                
        # Parse the args
        if not args:
            self.execute_finish("FAIL")
            return
        else:
            ret = self.service.execute(args)
            response = "OK"
            if ret not None:
                package = pickle.dumps(ret,2)
                response += " PICKLE %s" package
            self.execute_finish(response)
            return
    
    def execute_finish(self, msg):
        self.sendString("EXECUTE %s" % msg)
        self._reset()
    
    
    def handle_RESET(self, args):
        log.msg("Resettng the kernel...")
        self.factory.reset()
        self.sendString('RESET OK')
        self._reset()
    
    def handle_KILL(self, args):
        log.msg("Killing the kernel...")
        reactor.stop()
    
    def handle_DISCONNECT(self,args):
        log.msg("Disconnecting client...")
        self.sendString("DISCONNECT OK")
        self.transport.loseConnection()
    
