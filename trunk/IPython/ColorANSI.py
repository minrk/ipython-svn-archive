"""Tools for coloring text in ANSI terminals."""

#*****************************************************************************
#       Copyright (C) 2002 Fernando Pérez. <fperez@pizero.colorado.edu>
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

__author__ = 'Fernando Pérez. <fperez@pizero.colorado.edu>'
__version__ = '0.1.0'
__license__ = 'LGPL'
__date__   = 'Sat May 18 12:24:48 MDT 2002'

__all__ = ['TermColors','ColorScheme','ColorSchemeTable']

import os
from UserDict import UserDict
from Struct import Struct

class TermColors:
    """Color escape sequences.

    Defines the escape sequences for all the standard (ANSI?) colors in
    terminals. Also defines a NoColor escape which is just the null string,
    suitable for defining 'dummy' color schemes in terminals which get
    confused by color escapes.

    This class should be used as a mixin for building color schemes."""
    
    NoColor = ''  # for color schemes in color-less terminals.

    # Try to set color escapes which work across various types of terminals.
    # Problem: we need to wrap the escapes in \001..\002 for long lines not to
    # wrap in random ways, but \001,\002 generate on-screen garbage in old
    # xterms and Emacs terminals. I'd love to hear of a general solution.

    # New approach.  Let's see if this (checking for COLORTERM) works also for
    # WinXP.  It seems ok in Linux for konsole, xterm, rxvt, gnome-terminal
    # and emacs.  Need to also check with Andrea about OSX.

    # Note that the fix works ok for xterms in terms of not giving garbage,
    # but the line-wrapping problem persists.  Basically terminals which don't
    # honor the full ANSI escapes will necessarily have broken line-wrapping
    # for long lines.  There's just no way that I can find to have _both_
    # color and proper line wrapping on certain terminals.

    if os.environ.has_key('COLORTERM') or \
           os.environ.get('TERM')=='linux':
        #print '*** color: correct line wrapping'  # dbg
        Normal = '\001\033[0m\002'   # Reset normal coloring
        _base  = '\001\033[%sm\002'  # Template for all other colors
    else:
        #print '*** color: broken line wrapping'  # dbg
        Normal = '\033[0m'   # Reset normal coloring
        _base  = '\033[%sm'  # Template for all other colors

    # Name table for the color escapes
    # The 2; are needed for some terminals (CDE) to properly reset to dark colors
    Black        = _base % '0;2;30'
    Red          = _base % '0;2;31'
    Green        = _base % '0;2;32'
    Brown        = _base % '0;2;33'
    Blue         = _base % '0;2;34'
    Purple       = _base % '0;2;35'
    Cyan         = _base % '0;2;36'
    LightGray    = _base % '0;2;37'
    DarkGray     = _base % '1;30'
    LightRed     = _base % '1;31'
    LightGreen   = _base % '1;32'
    Yellow       = _base % '1;33'
    LightBlue    = _base % '1;34'
    LightPurple  = _base % '1;35'
    LightCyan    = _base % '1;36'
    White        = _base % '1;37'
    

class ColorScheme:
    """Generic color scheme class. Just a name and a Struct."""
    def __init__(self,__scheme_name_,colordict=None,**colormap):
        self.name = __scheme_name_
        if colordict is None:
            self.colors = Struct(**colormap)
        else:
            self.colors = Struct(colordict)
        
class ColorSchemeTable(UserDict):
    """General class to handle tables of color schemes.

    It's basically a dict of color schemes with a couple of shorthand
    attributes and some convenient methods.
    
    active_scheme_name -> obvious
    active_colors -> actual color table of the active scheme"""

    def __init__(self,scheme_list=None,default_scheme=''):
        """Create a table of color schemes.

        The table can be created empty and manually filled or it can be
        created with a list of valid color schemes AND the specification for
        the default active scheme.
        """
        
        UserDict.__init__(self)
        if scheme_list is None:
            self.active_scheme_name = ''
            self.active_colors = None
        else:
            if default_scheme == '':
                raise ValueError,'you must specify the default color scheme'
            for scheme in scheme_list:
                self.add_scheme(scheme)
            self.set_active_scheme(default_scheme)

    def add_scheme(self,new_scheme):
        """Add a new color scheme to the table."""
        if not isinstance(new_scheme,ColorScheme):
            raise ValueError,'ColorSchemeTable only accepts ColorScheme instances'
        self[new_scheme.name] = new_scheme
        
    def set_active_scheme(self,scheme,case_sensitive=0):
        """Set the currently active scheme.

        Names are by default compared in a case-insensitive way, but this can
        be changed by setting the parameter case_sensitive to true."""

        scheme_list = self.keys()
        if case_sensitive:
            valid_schemes = scheme_list
            scheme_test = scheme
        else:
            valid_schemes = [s.lower() for s in scheme_list]
            scheme_test = scheme.lower()
        try:
            scheme_idx = valid_schemes.index(scheme_test)
        except ValueError:
            raise ValueError,'Unrecognized color scheme: ' + scheme + \
                  '\nValid schemes: '+str(scheme_list).replace("'', ",'')
        else:
            active = scheme_list[scheme_idx]
            self.active_scheme_name = active
            self.active_colors = self[active].colors
            # Now allow using '' as an index for the current active scheme
            self[''] = self[active]
