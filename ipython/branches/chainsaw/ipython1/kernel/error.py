"""Classes and functions for kernel related errors and exceptions.

Classes:

NotDefined -- A class to represent a nonexistant python variable.
"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from ipython1.core import error

class KernelError(error.IPythonError)

class NotDefined(KernelError):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<NotDefined: %s>' % self.name

class IdInUse(KernelError):
    pass
    

class ProtocolError(KernelError):
    pass
    
class InvalidEngineID(KernelError):
    pass
    

    


