# -*- coding: iso-8859-1 -*-
"""pysh --- shell-like extensions for IPython.
"""

#*****************************************************************************
#       Copyright (C) 2004 Fernando PÃ©rez. <fperez@colorado.edu>
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

__author__ = 'Fernando PÃ©rez. <fperez@colorado.edu>'
__license__= 'LGPL'

import os,sys,shutil
import IPython.Extensions.InterpreterExec
from IPython.genutils import system,getoutput,getoutputerror

def shell():
    """
    This profile loads a set of modules and facilities to make shell-like
    usage with Python syntax more convenient.

    In particular, any lines which begin with ~/, ./ and /. will be executed
    as shell commands instead of as Python code.

    The os, sys and shutil modules from the Python standard library are
    automatically loaded.  Some additional IPython features, useful for shell
    usage, are listed below.  You can request more help about them with '?'.

    !cmd           - passes 'cmd' directly to the shell
    !!cmd          - executes 'cmd' and returns output as python list
    @sc var=cmd    - store output of 'cmd' in 'var'
    @sx cmd        - alias for !!cmd
    system         - execute a command in the underlying system shell
    getoutput      - capture the output of a system command
    getoutputerror - capture (output,error) of a system command
    """
    pass

print """Welcome to pysh, a set of extensions to IPython for shell usage.
    help(shell) -> help on the installed shell extensions.
    """
