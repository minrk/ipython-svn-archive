# -*- coding: iso-8859-1 -*-
"""pysh --- shell-like extensions for IPython.
"""

#*****************************************************************************
#       Copyright (C) 2004 Fernando Perez. <fperez@colorado.edu>
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

__author__ = 'Fernando Perez. <fperez@colorado.edu>'
__license__= 'LGPL'

# This module contains the bulk of the core changes.  By importing it we
# benefit from python's bytecode compilation
from IPython.Extensions.InterpreterExec import *

# Configure a few things.  Much of this is fairly hackish, since IPython
# doesn't really expose a clean API for it.  Be careful if you start making
# many modifications here.

print """\
Welcome to pysh, a set of extensions to IPython for shell usage.
help(pysh) -> help on the installed shell extensions and syntax.
"""

#  Set the 'cd' command to quiet mode, a more shell-like behavior
__IPYTHON__.default_option('cd','-q')

# Load all of $PATH as aliases
if os.name == 'posix':
    # %rehash is very fast, but it doesn't check for executability, it simply
    # dumps everything in $PATH as an alias. Use rehashx if you want more
    # checks.
    __IPYTHON__.magic_rehash()
else:
    # Windows users: the list of extensions considered executable is read from
    # the environment variable 'pathext'.  If this is undefined, IPython
    # defaults to EXE, COM and BAT.
    # %rehashx is the one which does extension analysis, at the cost of
    # being much slower than %rehash.
    __IPYTHON__.magic_rehashx()

# Remove %sc,%sx if present as aliases
__IPYTHON__.magic_unalias('sc')
__IPYTHON__.magic_unalias('sx')

# Reorder the tab-completion priorities
__IPYTHON__.Completer.matchers = ['file_matches','alias_matches','python_matches']

# We need different criteria for line-splitting, so that aliases such as
# 'gnome-terminal' are interpreted as a single alias instead of variable
# 'gnome' minus variable 'terminal'.
import re
__IPYTHON__.line_split = re.compile(r'(^[\s*!\?%,/]?)([\?\w\.\-\+]+\w*\s*)(\(?.*$)')

# Namespace cleanup
del re
