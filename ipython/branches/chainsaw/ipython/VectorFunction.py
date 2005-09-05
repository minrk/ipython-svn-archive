#****************************************************************************
#       Copyright (C) 2005 Brian Granger. <bgranger@scu.edu>
#
#  Distributed under the terms of the BSD License.  
#****************************************************************************

class VectorFunction:
    def __init__(self,funcname,cluster):
        self.funcname = funcname
        self.cluster = cluster
        
    def __call__(self,sequence):
        return self.cluster.map(self.funcname,sequence)


