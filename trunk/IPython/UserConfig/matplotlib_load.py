# -*- coding: iso-8859-1 -*-
"""matlab-like functionality based on John Hunter's matplotlib library.

This loads matplotlib in interactive mode, but it FORCES the use of the TkAgg
backend when running under a non-multithreaded IPython.  This is necessary
because the GTK and WX backends require special handling of the GUI thread to
avoid blocking.

IPython now ships with thread support so all backends can be used, but the
threading needs to be specifically activated.  For full threaded matplotlib
support, use 'ipython -mpthread ...more options...' """

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

__author__ = 'Fernando Perez. <Fernando.Perez@colorado.edu>'
__license__= 'LGPL'

# Load matplotlib, set backend and interactivity.
# THESE MUST BE THE FIRST MATPLOTLIB COMMANDS CALLED!
import matplotlib

# A normal ipython (without matplotlib thread support) can only use the Tk
# backend, since all others require special handling of the gui thread
import IPython.Shell
if not isinstance(__IPYTHON__,IPython.Shell.MatplotlibShell) and \
       not matplotlib.rcParams['backend'].startswith('Tk'):
    import IPython.genutils as gu
    gu.warn('Forcing TkAgg backend (others require the multithreaded IPython).')
    matplotlib.use('TkAgg')

matplotlib.interactive(True)

# Now we can continue with other code...

# Load these by themselves so that 'help MODULE' works
import matplotlib.matlab as matlab

# Bring all of the numeric and plotting commands to the toplevel namespace
from matplotlib.matlab import *

# IPython.numutils has hardwired Numeric stuff; matplotlib knows what
# numerical library the user has via the 'numerix' parameter:
if matplotlib.rcParams['numerix'] == 'Numeric':
    from IPython.numutils import *

print """Welcome to pylab, a matlab-like python environment.
    help(matlab)   -> help on matlab compatible commands from matplotlib.
    help(plotting) -> help on plotting commands.
    """
