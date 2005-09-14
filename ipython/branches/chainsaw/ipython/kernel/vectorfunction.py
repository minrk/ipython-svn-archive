#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************
"""Classse that allow functions to operate in a sequence in parallel.

Classes:

VectorFunction -- A basic vetorized function
"""

class VectorFunction:
    def __init__(self,funcname,cluster):
        self.funcname = funcname
        self.cluster = cluster
        
    def __call__(self,sequence):
        return self.cluster.map(self.funcname,sequence)


