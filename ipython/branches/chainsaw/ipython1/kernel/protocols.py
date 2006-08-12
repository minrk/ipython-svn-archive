#*****************************************************************************
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from twisted.protocols import basic

class EnhancedNetstringReceiver(basic.NetstringReceiver):
    
    def sendBuffer(self, buf):
        bufLength = len(buf)
        self.transport.write('%d:')
        self.transport.write(buf)
        self.transport.write(',')