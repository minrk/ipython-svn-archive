"""Classes used in scattering sequences.

Scattering consists of partitioning a sequence and sending the various
pieces to individual nodes in a cluster.
"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

class Map:
            
    def getPartition(self, seq, p, q):
        """Returns the pth partition of q partitions of seq."""
        
        # Test for error conditions here
        if p<0 or p>=q:
          print "No partition exists."
          return
          
        remainder = len(seq)%q
        basesize = len(seq)/q
        hi = []
        lo = []
        for n in range(q):
            if n < remainder:
                lo.append(n * (basesize + 1))
                hi.append(lo[-1] + basesize + 1)
            else:
                lo.append(n*basesize + remainder)
                hi.append(lo[-1] + basesize)

        result = self.seq[lo[p]:hi[p]]
   

    def joinPartitions(self, listOfPartitions):
        return listOfSequences

class RoundRobinScatter(BasicScatter):

    def partition(self, p, q):
        result = []
        for i in range(p,len(self.seq),q):
            result.append(self.seq[i])
        if self.flatten and len(result) ==  1:
            return result[0]
        else:          
            return result          

    def departition(self, listOfSequences, flatten=True):
        return listOfSequences

styles = {'basic':BasicScatter, 'roundrobin':RoundRobinScatter}

    
    
