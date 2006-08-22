#*****************************************************************************
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from twisted.protocols import basic

class EnhancedNetstringReceiver(basic.NetstringReceiver, object):

    MAX_LENGTH = 500000000

    def sendBuffer(self, buf):
        self.transport.write('%i:' %len(buf))
        
        # want to be able to call:
        # self.transport.write(buf)
        # but can't, so we have a
        # temporary solution that copies:
        self.transport.write(str(buf))
        self.transport.write(',')