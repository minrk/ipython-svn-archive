# -*- coding: iso-8859-1 -*-
"""Tools for inspecting Python objects.

Uses syntax highlighting for presenting the various information elements.

Similar in spirit to the inspect module, but all calls take a name argument to
reference the name under which an object is being read.

$Id$
"""

#*****************************************************************************
#       Copyright (C) 2002 Fernando Pérez. <fperez@colorado.edu>
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
__version__ = '0.1.0'
__license__ = 'LGPL'
__date__   = 'Sat May 18 12:24:48 MDT 2002'

__all__ = ['Inspector','InspectColors']

import inspect,linecache,types,StringIO,string
from Itpl import itpl
from genutils import page,indent,Term
import PyColorize
from IPython.ColorANSI import *

#****************************************************************************
# Builtin color schemes

Colors = TermColors  # just a shorthand

# Build a few color schemes
NoColor = ColorScheme(
    'NoColor',{
    'header' : Colors.NoColor,
    'normal' : Colors.NoColor  # color off (usu. Colors.Normal)
    }  )

LinuxColors = ColorScheme(
    'Linux',{
    'header' : Colors.LightRed,
    'normal' : Colors.Normal  # color off (usu. Colors.Normal)
    } )

LightBGColors = ColorScheme(
    'LightBG',{
    'header' : Colors.Red,
    'normal' : Colors.Normal  # color off (usu. Colors.Normal)
    }  )

# Build table of color schemes (needed by the parser)
InspectColors = ColorSchemeTable([NoColor,LinuxColors,LightBGColors],
                                 'Linux')

#****************************************************************************
# Class definitions

class myStringIO(StringIO.StringIO):
    """Adds a writeln method to normal StringIO."""
    def writeln(self,*arg,**kw):
        """Does a write() and then a write('\n')"""
        self.write(*arg,**kw)
        self.write('\n')

class Inspector:
    def __init__(self,color_table,code_color_table,scheme):
        self.color_table = color_table
        self.parser = PyColorize.Parser(code_color_table,out='str')
        self.format = self.parser.format
        self.set_active_scheme(scheme)

    def __getargspec(self,obj):
        """Get the names and default values of a function's arguments.

        A tuple of four things is returned: (args, varargs, varkw, defaults).
        'args' is a list of the argument names (it may contain nested lists).
        'varargs' and 'varkw' are the names of the * and ** arguments or None.
        'defaults' is an n-tuple of the default values of the last n arguments.

        Modified version of inspect.getargspec from the Python Standard
        Library."""

        if inspect.isfunction(obj):
            func_obj = obj
        elif inspect.ismethod(obj):
            func_obj = obj.im_func
        else:
            raise TypeError, 'arg is not a Python function'
        args, varargs, varkw = inspect.getargs(func_obj.func_code)
        return args, varargs, varkw, func_obj.func_defaults

    def __getdef(self,obj,oname=''):
        """Return the definition header for any callable object."""

        # We don't trap any inspect exceptions here, it's the caller's role to
        # handle those.  In fact, caller code may use a generated exception to
        # inform that definition headers aren't available.
        return oname + inspect.formatargspec(*self.__getargspec(obj))
 
    def __head(self,h):
        """Return a header string with proper colors."""
        return '%s%s%s' % (self.color_table.active_colors.header,h,
                           self.color_table.active_colors.normal)

    def set_active_scheme(self,scheme):
        self.color_table.set_active_scheme(scheme)
        self.parser.color_table.set_active_scheme(scheme)
    
    def noinfo(self,msg,oname):
        """Generic message when no information is found."""
        print 'No %s found' % msg,
        if oname:
            print 'for %s' % oname
        else:
            print
            
    def pdef(self,obj,oname=''):
        """Print the definition header for any callable object.

        If the object is a class, print the constructor information."""

        if not callable(obj):
            print 'Object is not callable.'
            return

        header = ''
        if type(obj) is types.ClassType:
            header = self.__head('Class constructor information:\n')
            obj = obj.__init__
        elif type(obj) is types.InstanceType:
            obj = obj.__call__
        try:
            output =  self.format(self.__getdef(obj,oname))
        except:
            self.noinfo('definition header',oname)
        else:
            print >>Term.cout, header,output,

    def pdoc(self,obj,oname='',formatter = None):
        """Print the docstring for any object.

        Optional:
        -formatter: a function to run the docstring through for specially
        formatted docstrings."""
        
        head = self.__head  # so that itpl can find it even if private
        if formatter is None:
            ds = inspect.getdoc(obj)
        else:
            ds = formatter(inspect.getdoc(obj))
        if type(obj) is types.ClassType:
            init_ds = inspect.getdoc(obj.__init__)
            output = itpl('$head("Class Docstring:")\n'
                          '$indent(ds)\n'
                          '$head("Constructor Docstring"):\n'
                          '$indent(init_ds)')
        elif type(obj) is types.InstanceType and hasattr(obj,'__call__'):
            call_ds = inspect.getdoc(obj.__call__)
            if call_ds:
                output = itpl('$head("Class Docstring:")\n$indent(ds)\n'
                              '$head("Calling Docstring:")\n$indent(call_ds)')
            else:
                output = ds
        else:
            output = ds
        if output == None:
            self.noinfo('documentation',oname)
            return
        page(output)

    def psource(self,obj,oname=''):
        """Print the source code for an object."""

        # Flush the source cache because inspect can return out-of-date source
        linecache.checkcache()
        try:
            src = inspect.getsource(obj) 
        except:
            self.noinfo('source',oname)
        else:
            page(self.format(src))

    def pfile(self,obj,oname=''):
        """Show the whole file where an object was defined."""
        try:
            sourcelines,lineno = inspect.getsourcelines(obj)
        except:
            self.noinfo('file',oname)
        else:
            # run contents of file through pager starting at line
            # where the object is defined            
            page(self.format(open(inspect.getabsfile(obj)).read()),lineno)
        
    def pinfo(self,obj,oname='',ospace='',formatter = None, detail_level=0,
              ismagic=0):
        """Show detailed information about an object.

        Optional arguments:
        
        - ospace: name of the namespace where object is defined.
        - formatter: special formatter for docstrings (see pdoc)
        - detail_level: if set to 1, more information is given.
        - ismagic: special parameter for IPython's magic functions.
        """

        header = self.__head
        ds = indent(inspect.getdoc(obj))
        if formatter is not None:
            ds = formatter(ds)

        # store output in a list which gets joined with \n at the end.
        out = myStringIO()
        
        string_max = 200 # max size of strings to show (snipped if longer)
        shalf = int((string_max -5)/2)

        if ismagic:
            obj_type = 'Magic function'
        else:
            obj_type = type(obj).__name__
        out.writeln(header('Type:\t\t')+obj_type)

        try:
            bclass = obj.__class__
            out.writeln(header('Base Class:\t')+str(bclass))
        except: pass

        # String form, but snip if too long in ? form (full in ??)
        try:
            ostr = str(obj)
            str_head = 'String Form:'
            if not detail_level and len(ostr)>string_max:
                ostr = ostr[:shalf] + ' <...> ' + ostr[-shalf:]
                ostr = ("\n" + " " * len(str_head.expandtabs())).\
                       join(map(string.strip,ostr.split("\n")))
            if ostr.find('\n') > -1:
                # Print multi-line strings starting at the next line.
                str_sep = '\n'
            else:
                str_sep = '\t'
            out.writeln("%s%s%s" % (header(str_head),str_sep,ostr))
        except:
            pass

        if ospace:
            out.writeln(header('Namespace:\t')+ospace)

        # Length (for strings and lists)
        try:
            length = str(len(obj))
            out.writeln(header('Length:\t\t')+length)
        except: pass

        # Filename where object was defined
        try:
            file = inspect.getabsfile(obj)
            if file.endswith('<string>'):
                file = 'Dynamically generated function. No source code available.'
            out.writeln(header('File:\t\t')+file)
        except: pass

        # reconstruct the function definition and print it:
        try:
            defln = self.__getdef(obj,oname)
        except:
            pass
        else:
            out.write(header('Definition:\t')+self.format(defln))
 
        # Docstrings only in detail 0 mode (unless source fails, see below)
        if ds and detail_level == 0:
                out.writeln(header('Docstring:\n') + ds)

        # Original source code for any callable
        if detail_level:
            # Flush the source cache because inspect can return out-of-date source
            linecache.checkcache()
            try:
                source = self.format(inspect.getsource(obj))
                out.write(header('Source:\n')+source.rstrip())
            except:
                if ds:
                    out.writeln(header('Docstring:\n') + ds)

        # Constructor docstring for classes
        if type(obj) is types.ClassType:
            # reconstruct the function definition and print it:
            gotdef = init_ds = 0
            try:
                init_def = self.__getdef(obj.__init__,oname)
                gotdef = 1
            except:
                gotdef = 0
            try:
                init_ds = inspect.getdoc(obj.__init__)
            except:
                init_ds = None

            if gotdef or init_ds:
                out.writeln(header('\nConstructor information:'))
                if gotdef:
                    out.write(header('Definition:\t')+ self.format(init_def))
                if init_ds:
                    out.writeln(header('Docstring:\n') + indent(init_ds))

        # Call form docstring for callable instances
        if type(obj) is types.InstanceType and hasattr(obj,'__call__'):
            out.writeln(header('Callable:\t')+'Yes')
            try:
                call_def = self.__getdef(obj.__call__,oname)
            except TypeError:
                # Some callables may raise a TypeError if inspect's
                # isfunction and ismethod can't identify them.
                out.write(header('Call def:\t')+
                          'Calling definition not available.')
            else:
                out.write(header('Call def:\t')+self.format(call_def))
            call_ds = inspect.getdoc(obj.__call__)
            if call_ds:
                out.writeln(header('Call docstring:\n') + indent(call_ds))

        # Finally send to printer/pager
        output = out.getvalue()
        if output:
            page(output)
        # end pinfo
