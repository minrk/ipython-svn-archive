# encoding: utf-8
"""Utilities for PB using modules.
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

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import cPickle as pickle

from twisted.python.failure import Failure
from twisted.python import failure

from ipython1.kernel import pbconfig
from ipython1.kernel.error import PBMessageSizeError


#-------------------------------------------------------------------------------
# The actual utilities
#-------------------------------------------------------------------------------

def packageFailure(f):
    """Clean and pickle a failure preappending the string FAILURE:"""
    
    f.cleanFailure()
    # This is sometimes helpful in debugging
    #f.raiseException()
    pString = pickle.dumps(f, 2)
    return 'FAILURE:' + pString

def checkMessageSize(m, info):
    """Check string m to see if it violates banana.SIZE_LIMIT.
    
    This should be used on the client side of things for push, scatter
    and pushSerialized and on the other end for pull, gather and pullSerialized.
    
    :Parameters:
        `m` : string
            Message whose size will be checked.
        `info` : string
            String describing what object the message refers to.
            
    :Exceptions:
        - `PBMessageSizeError`: Raised in the message is > banana.SIZE_LIMIT

    :returns: The original message or a Failure wrapping a PBMessageSizeError
    """

    if len(m) > pbconfig.banana.SIZE_LIMIT:
        s = """Objects too big to transfer:
Names:            %s
Actual Size (kB): %d
SIZE_LIMIT  (kB): %d
* SIZE_LIMIT can be set in kernel.pbconfig""" \
            % (info, len(m)/1024, pbconfig.banana.SIZE_LIMIT/1024)
        return Failure(PBMessageSizeError(s))
    else:
        return m