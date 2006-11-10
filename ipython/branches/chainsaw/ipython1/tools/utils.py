# encoding: utf-8
"""Generic utilities for use by IPython's various subsystems.
"""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#       Copyright (C) 2006  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#---------------------------------------------------------------------------
# Stdlib imports
#---------------------------------------------------------------------------

import os
import sys

#---------------------------------------------------------------------------
# Normal code begins
#---------------------------------------------------------------------------

def extractVars(*names,**kw):
    """Extract a set of variables by name from another frame.

    :Parameters:
      - `*names`: strings
        One or more variable names which will be extracted from the caller's
    frame.

    :Keywords:
      - `depth`: integer (0)
        How many frames in the stack to walk when looking for your variables.


    Examples:

        >>> def func(x):
        ...     y = 1
        ...     print extractVars('x','y')
        ...

        >>> func('some string')
        {'y': 1, 'x': 'some string'}
    """

    depth = kw.get('depth',0)
    
    callerNS = sys._getframe(depth+1).f_locals
    return dict((k,callerNS[k]) for k in names)
    

def extractVarsAbove(*names):
    """Extract a set of variables by name from another frame.

    Similar to extractVars(), but with a specified depth of 1, so that names
    are exctracted exactly from above the caller.

    This is simply a convenience function so that the very common case (for us)
    of skipping exactly 1 frame doesn't have to construct a special dict for
    keyword passing."""

    callerNS = sys._getframe(2).f_locals
    return dict((k,callerNS[k]) for k in names)
    
def shexp(s):
    "Expand $VARS and ~names in a string, like a shell"
    return os.path.expandvars(os.path.expanduser(s))
    
