#*****************************************************************************
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from twisted.protocols import basic
from twisted.internet import protocol

class EnhancedNetstringReceiver(basic.NetstringReceiver, object):
    
    MAX_LENGTH = 134217728 # 100 MB, 2**27

    def sendBuffer(self, buf):
        self.transport.write('%i:' %len(buf))
        
        # want to be able to call:
        # self.transport.write(buf)
        # but can't, so we have a
        # temporary solution that copies:
        self.transport.write(str(buf))
        self.transport.write(',')
    

class EnhancedFactory:
    
    MAX_LENGTH = 134217728 # 100 MB, 2**27
    
    def buildProtocol(self, addr):
        p = self.protocol()
        p.MAX_LENGTH = self.MAX_LENGTH
        p.factory = self
        return p
    

class EnhancedServerFactory(EnhancedFactory, protocol.ServerFactory, object):
    pass

class EnhancedClientFactory(EnhancedFactory, protocol.ClientFactory, object):
    pass

    
    