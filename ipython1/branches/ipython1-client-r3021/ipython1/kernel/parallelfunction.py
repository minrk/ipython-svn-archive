# encoding: utf-8
"""
A parallelized function that does scatter/execute/gather.
"""
__docformat__ = "restructuredtext en"
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelley <benjaminrk@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

from types import FunctionType

class ParallelFunction:
    """A function that operates in parallel on sequences."""
    def __init__(self, targets, func, remoteController):
        """Create a `ParallelFunction`.
        """
        assert isinstance(func, (str, FunctionType)), "func must be a fuction or str"
        self.func = func
        self.rc = remoteController
        self.targets = targets
        
    def __call__(self,sequence):
        return self.rc.map(self.targets, self.func, sequence)