"""Classes and functions for kernel related errors and exceptions.
"""
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

from ipython1.core import error

#-------------------------------------------------------------------------------
# Error classes
#-------------------------------------------------------------------------------

class KernelError(error.IPythonError):
    pass

class NotDefined(KernelError):
    def __init__(self, name):
        self.name = name
        self.args = (name,)

    def __repr__(self):
        return '<NotDefined: %s>' % self.name
    
    __str__ = __repr__

class QueueCleared(KernelError):
    pass

class IdInUse(KernelError):
    pass

class ProtocolError(KernelError):
    pass
    
class InvalidEngineID(KernelError):
    pass
    

    


