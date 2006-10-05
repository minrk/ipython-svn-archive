#!/usr/bin/env python
# encoding: utf-8
"""
A parallelized function that does scatter/execute/gather.
"""
__docformat__ = "restructuredtext en"
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

class ParallelFunction:
    def __init__(self, functionName, remoteController):
        self.fname = functionName
        self.rc = remoteController
        
    def __call__(self,sequence):
        return self.rc.mapAll(self.fname,sequence)