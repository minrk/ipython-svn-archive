# -*- coding: iso-8859-1 -*-
"""pysh --- shell-like extensions for IPython.
"""

#*****************************************************************************
#       Copyright (C) 2004 Fernando Pérez. <fperez@colorado.edu>
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

__author__ = 'Fernando Pérez. <fperez@colorado.edu>'
__license__= 'LGPL'

import IPython.Extensions.InterpreterExec
from IPython.genutils import system,getoutput,getoutputerror

def shell():
    """
    This profile loads a special input line filter to allow executing as shell
    commands any lines which begin with ~/, ./ and /.

    The following functions are also loaded from IPython.genutils.  You can
    request more help about each one of them:

    system         - execute a command in the underlying system shell.
    getoutput      - capture the output of a system command.
    getoutputerror - capture (output,error) of a system command.
    """
    pass

print """Welcome to pysh, a set of extensions to IPython for shell usage.
    help(shell)  -- help on the installed shell extensions."""
