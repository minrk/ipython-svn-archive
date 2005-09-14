"""Classes used in scattering sequences.

Scattering consists of partitioning a sequence and sending the various
pieces to individual nodes in a cluster.

Classes:

Scatter -- The basic class for scattering sequences
"""


#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************


class Scatter:
    def __init__(self,seq,balance=0):
        self.seq = seq
            
    def partition(self, p, q):
        """Returns the pth partition of q partitions."""
        
        # Test for error conditions here
        if p<0 or p>=q:
          print "No partition exists."
          return
          
        remainder = len(self.seq)%q
        basesize = len(self.seq)/q
        hi = []
        lo = []
        for n in range(q):
            if n < remainder:
                lo.append(n * (basesize + 1))
                hi.append(lo[-1] + basesize + 1)
            else:
                lo.append(n*basesize + remainder)
                hi.append(lo[-1] + basesize)

        return self.seq[lo[p]:hi[p]]
            
