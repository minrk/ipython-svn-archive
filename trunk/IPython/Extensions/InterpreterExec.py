# -*- coding: iso-8859-1 -*-
"""Modified input prompt for executing files.

We define a special input line filter to allow typing lines which begin with
'~/', '/' or './'. If one of those strings is encountered, it is automatically
executed.

All other input is processed normally."""

#*****************************************************************************
#       Copyright (C) 2001 Fernando Pérez. <fperez@colorado.edu>
#
#  Distributed under the terms of the GNU Lesser General Public License (LGPL)
#
#    This code is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#  The full text of the LGPL is available at:
#
#                  http://www.gnu.org/copyleft/lesser.html
#*****************************************************************************

__author__ = 'W.J. van der Laan <gnufnork@hetdigitalegat.nl>'
__version__= '0.1.0'
__license__= 'LGPL'
__date__   = 'Tue Jan 27 18:56:01 CET 2004'

def prefilter_paste(self,line,continuation):
    """Alternate prefilter for input of pasted code from an interpreter.
    """

    from IPython.iplib import InteractiveShell
    if line.startswith("~/") or line.startswith("./") or line.startswith("/"):
        return InteractiveShell._prefilter(self,"!"+line,continuation)
    else:
        return InteractiveShell._prefilter(self,line,continuation)

# Rebind this to be the new IPython prefilter:
from IPython.iplib import InteractiveShell
InteractiveShell.prefilter = prefilter_paste

# Clean up the namespace.
del InteractiveShell,prefilter_paste
