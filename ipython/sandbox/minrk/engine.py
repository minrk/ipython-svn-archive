"""protocol and factory adapted from kernel1p.kernelcore for ipengine"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************
import cPickle as pickle

from twisted.protocols import basic

class ControlProtocol(basic.Int32StringReceiver):
    
    def connectionMade(self):
        log.msg("Connection Made...")
        self.transport.setTcpNoDelay(True)
        peer = self.transport.getPeer()
#        if not self.factory.is_allowed(peer.host):
#            log.msg("Denied Client: %s" % peer.host)
#            self.transport.loseConnection()
    
    def stringReceived(self, string):
        split_string = string.split(" ", 1)
        if len(split_string) == 1:
            cmd = split_string[0]
            args = None
        elif len(split_string) == 2:
            cmd = split_string[0]
            args = split_string[1]
            
            f = getattr(self, 'handle_%s' %
                (cmd), None)
            if f:
                # Handler resolved with cmd
                f(args)
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
                (key, value) = args.split('=')
                self.factory.put(key,value)
            except:
                self.put_finish("FAIL")
                return
                
            self.put_finish("OK")
    
    def put_finish(self,msg):
        self.sendString("PUT %s" % msg)
        self._reset()
    
    def handle_putPickle(self, string):
        if not args:
            self.putPickle_finish("FAIL")
            return
        else:
            try: 
                (key, value) = args.split('=')
                self.factory.putPickle(key,pickle.dumps(value, 2))
            except:
                self.putPickle_finish("FAIL")
                return
                
            self.put_finish("OK")
    
    def putPickle_finish(self,msg):
        self.sendString("PUTPICKLE %s" % msg)
        self._reset()
    
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
                package = self.factory.getPickle(args)
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
            ret = self.factory.execute(args)
            response = "OK"
            if ret not None:
                package = pickle.dumps(ret,2)
                response += " PICKLE %s" package
            self.execute_finish(response)
            return
    
    def execute_finish(self, msg):
        self.sendString("EXECUTE %s" % msg)
        self._reset()
    
    
#    def handle_RESET(self, args):
#        log.msg("Resettng the kernel...")
#        self.factory.reset()
#        self.sendString('RESET OK')
#        self._reset()
    
#    def handle_KILL(self, args):
#        log.msg("Killing the kernel...")
#        reactor.stop()
    
#    def handle_DISCONNECT(self,args):
#        log.msg("Disconnecting client...")
#        self.sendString("DISCONNECT OK")
#        self.transport.loseConnection()
    
