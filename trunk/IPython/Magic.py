"""Magic functions for InteractiveShell.

$Id$
"""

from __future__ import nested_scopes

#*****************************************************************************
#       Copyright (C) 2001 Janko Hauser <jhauser@ifm.uni-kiel.de> and
#                          Fernando P�rez <fperez@pizero.colorado.edu>
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

#****************************************************************************
# Modules and globals

import Release
__version__ = Release.version
__date__    = Release.date
__author__  = '%s <%s>\n%s <%s>' % \
              ( Release.authors['Janko'] + Release.authors['Fernando'] )
__license__ = Release.license

# Python standard modules
import __builtin__
import os, sys, inspect, pydoc, re, tempfile, profile, pstats
from getopt import getopt
from pprint import pprint, pformat
from cStringIO import StringIO

# Homebrewed
from genutils import *
from Struct import Struct
from Itpl import Itpl, itpl, printpl
from FakeModule import FakeModule

#***************************************************************************
# Utility functions
def magic2python(cmd):
    """Convert a command string of magic syntax to valid Python code."""

    if cmd.startswith('#@') or cmd.startswith('@'):
        if cmd[0]=='#':
            cmd = cmd[1:]
        # we need to return the proper line end later
        if cmd[-1] == '\n':
            endl = '\n'
        else:
            endl = ''
        try:
            func,args = cmd[1:].split(' ',1)
        except:
            func,args = cmd[1:].rstrip(),''
        args = args.replace('"','\\"').replace("'","\\'").rstrip()
        return '__IP.magic_%s ("%s")%s' % (func,args,endl)
    else:
        return cmd


def on_off(tag):
    """Return an ON/OFF string for a 1/0 input. Simple utility function."""
    return ['OFF','ON'][tag]


def get_py_filename(name):
    """Return a valid python filename in the current directory.

    If the given name is not a file, it adds '.py' and searches again.
    Raises IOError with an informative message if the file isn't found."""

    name = os.path.expanduser(name)
    if not os.path.isfile(name) and not name.endswith('.py'):
        name += '.py'
    if os.path.isfile(name):
        return name
    else:
        raise IOError,'File `%s` not found.' % name


#****************************************************************************
# Utility classes
class Profile(profile.Profile):
    """Add a string_stats method to the profile.Profile class.

    This allows the IPython profiler interaction functions to properly format
    profile results."""

    def string_stats(self):
        """Return the result of print_stats as a string."""
        sys.stdout.flush()
        sys_stdout = sys.stdout
        output = StringIO()
        try:
            sys.stdout = output
            self.print_stats()
        finally:
            sys.stdout = sys_stdout
            sys.stdout.flush()
        return output.getvalue()


class Macro:
    """Simple class to store the value of macros as strings.

    This allows us to later exec them by checking when something is an
    instance of this class."""
    
    def __init__(self,cmds):
        """Build a macro from a list of commands."""

        # Since the list may include multi-line entries, first make sure that
        # they've been all broken up before passing it to magic2python
        cmdlist = map(magic2python,''.join(cmds).split('\n'))
        self.value = '\n'.join(cmdlist)

    def __str__(self):
        return self.value


#***************************************************************************
# Main class implementing Magic functionality
class Magic:
    """Magic functions for InteractiveShell.

    Shell functions which can be reached as @function_name. All magic
    functions should accept a string, which they can parse for their own
    needs. This can make some functions easier to type, eg `@cd ../`
    vs. `@cd("../")`

    ALL definitions MUST begin with the prefix magic_. The user won't need it
    at the command line, but it is is needed in the definition. """

    # class globals
    auto_status = ['Automagic is OFF, @ prefix IS needed for magic functions.',
                   'Automagic is ON, @ prefix NOT needed for magic functions.']

    #......................................................................
    # some utility functions

    def __init__(self):
        self.alias_table = {}

    def lsmagic(self):
        """Return a list of currently available magic functions.

        Gives a list of the bare names after mangling (['ls','cd', ...], not
        ['magic_ls','magic_cd',...]"""

        # FIXME. This needs a cleanup, in the way the magics list is built.
        
        # magics in class definition
        class_magic = lambda fn: fn.startswith('magic_') and \
                      callable(Magic.__dict__[fn])
        # in instance namespace (run-time user additions)
        inst_magic =  lambda fn: fn.startswith('magic_') and \
                     callable(self.__dict__[fn])
        # and bound magics by user (so they can access self):
        inst_bound_magic =  lambda fn: fn.startswith('magic_') and \
                           callable(self.__class__.__dict__[fn])
        magics = filter(class_magic,Magic.__dict__.keys()) + \
                 filter(inst_magic,self.__dict__.keys()) + \
                 filter(inst_bound_magic,self.__class__.__dict__.keys())
        out = []
        for fn in magics:
            out.append(fn.replace('magic_','',1))
        out.sort()
        return out
    
    def set_shell(self,shell):
        self.shell = shell
    
    def getargspec(self,obj):
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

    def extract_input_slices(self,slices):
        """Return as a string a set of input history slices.

        The set of slices is given as a list of strings (like ['1','4:8','9'],
        since this function is for use by magic functions which get their
        arguments as strings."""

        cmds = []
        for chunk in slices:
            if ':' in chunk:
                ini,fin = map(int,chunk.split(':'))
            else:
                ini = int(chunk)
                fin = ini+1
            cmds.append(self.shell.input_hist[ini:fin])
        return cmds

    def _get_def(self,oname,obj):
        """Return the definition header for any callable object and a success flag."""

        # There used to be a lot of fancy code here, until I realized that the
        # proper way of calling formatargspec() is with a * in the args! Now
        # this function is trivial.
        try:
            return oname + inspect.formatargspec(*self.getargspec(obj)), 1
        except:
            return 'Could not get definition header for ' + `oname` , 0

    def _ofind(self,oname):
        """Find an object in the available namespaces.

        self._ofind(oname) -> dict with keys: found,obj,ospace,docstring,ismagic

        Has special code to detect magic functions.
        """

        # the @ in magics isn't really part of the name
        oname = oname.strip()
        if oname.startswith('@'):
            oname = oname[1:]

        # Namespaces to search in:
        user_ns        = self.shell.user_ns
        user_config_ns = self.shell.user_config_ns
        internal_ns    = self.shell.internal_ns
        builtin_ns     = __builtin__.__dict__

        # Put them in a list. The order is important so that we find things in the
        # same order that Python finds them.
        namespaces = [ ('Interactive',user_ns),
                       ('User-defined configuration',user_config_ns),
                       ('IPython internal',internal_ns),
                       ('Python builtin',builtin_ns)
                       ]

        # initialize results to 'null'
        found = 0; obj = None;  ospace = None;  ds = None; ismagic = 0

        try:
            for nsname,ns in namespaces:
                try:
                    obj = ns[oname]
                except KeyError:
                    pass
                else:
                    found = 1
                    ospace = nsname
                    ds = inspect.getdoc(obj)
                    raise 'found it'
        except 'found it':
            pass

        # try to see if it's magic
        if not found:
            try:
                obj = eval('self.magic_'+oname)
                found = 1
                ospace = 'IPython internal'
                ismagic = 1
                ds = inspect.getdoc(obj)
            except:
                pass
        # Play some games to try and find info about dotted objects
        # and for things like {}.get? or ''.remove? to work
        if not found:
            try:
                ns_test = namespaces[0]
                self.tmp_obj = eval(oname,ns_test[1])
                found = 1
            except:
                try:
                    ns_test = namespaces[3]
                    self.tmp_obj = eval(oname,ns_test[1])
                    found = 1
                except:
                    pass
            if found:
                ds = inspect.getdoc(self.tmp_obj)
                ospace = ns_test[0]
                obj = self.tmp_obj
                del self.tmp_obj

        #return found,obj,ospace,ds,ismagic
        return {'found':found, 'obj':obj, 'namespace':ospace,
                'docstring':ds, 'ismagic':ismagic}
        
    def arg_err(self,func):
        """Print docstring if incorrect arguments were passed"""
        print 'Error in arguments:'
        print inspect.getdoc(func)


    def format_latex(self,str):
        """Format a string for latex inclusion."""

        # Characters that need to be escaped for latex:
        escape_re = re.compile(r'(%|_|\$)',re.MULTILINE)
        # Magic command names as headers:
        cmd_name_re = re.compile(r'^(@.*?):',re.MULTILINE)
        # Magic commands 
        cmd_re = re.compile(r'(?P<cmd>@.+?\b)(?!\}\}:)',re.MULTILINE)
        # Paragraph continue
        par_re = re.compile(r'\\$',re.MULTILINE)

        str = cmd_name_re.sub(r'\n\\texttt{\\textbf{\1}}:',str)
        str = cmd_re.sub(r'\\texttt{\g<cmd>}',str)
        str = par_re.sub(r'\\\\',str)
        str = escape_re.sub(r'\\\1',str)
        #file('/home/fperez/ipython/doc/magic.tex','w').write(str)  # dbg
        return str

    def format_screen(self,str):
        """Format a string for screen printing.

        This removes some latex-type format codes."""
        # Paragraph continue
        par_re = re.compile(r'\\$',re.MULTILINE)
        str = par_re.sub('',str)
        return str

    def parse_options(self,arg_str,opt_str,*long_opts,**kw):
        """Parse options passed to an argument string.

        The interface is similar to that of getopt(), but it returns back a
        Struct with the options as keys and the stripped argument string still
        as a string.

        Options:
          -mode: default 'string'. If given as 'list', the argument string is
          returned as a list (split on whitespace) instead of a string.

          -list_all: put all option values in lists. Normally only options
          appearing more than once are put in a list."""

        mode = kw.get('mode','string')
        list_all = kw.get('list_all',0)

        opts,args = getopt(arg_str.split(),opt_str,*long_opts)
        odict = {}
        for o,a in opts:
            if o.startswith('--'):
                o = o[2:]
            else:
                o = o[1:]
            try:
                odict[o].append(a)
            except AttributeError:
                odict[o] = [odict[o],a]
            except KeyError:
                if list_all:
                    odict[o] = [a]
                else:
                    odict[o] = a
        opts = Struct(odict)

        if mode == 'string':
            args = ' '.join(args)
        elif mode == 'list':
            pass
        else:
            raise ValueError,'incorrect mode given:'+`mode`
        return opts,args
    
    #......................................................................
    # And now the actual magic functions

    # Functions for IPython shell work (vars,funcs, config, etc)
    def magic_lsmagic(self, parameter_s = ''):
        """List currently available magic functions."""
        print 'Available magic functions:\n@'+'  @'.join(self.lsmagic())
        print '\n' + Magic.auto_status[self.rc.automagic]
        return None
        
    def magic_magic(self, parameter_s = ''):
        """Print information about the magic function system."""

        mode = ''
        try:
            if parameter_s.split()[0] == '-latex':
                mode = 'latex'
        except:
            pass

        magic_docs = []
        for fname in self.lsmagic():
            mname = 'magic_' + fname
            for space in (Magic,self,self.__class__):
                try:
                    fn = space.__dict__[mname]
                except KeyError:
                    pass
                else:
                    break
            magic_docs.append('@%s:\n\t%s\n' %(fname,fn.__doc__))
        magic_docs = ''.join(magic_docs)

        if mode == 'latex':
            print self.format_latex(magic_docs)
            return
        else:
            magic_docs = self.format_screen(magic_docs)
        
        outmsg = """
IPython's 'magic' functions
===========================

The magic function system provides a series of functions which allow you to
control the behavior of IPython itself, plus a lot of system-type
features. All these functions are prefixed with a @ character, but parameters
are given without parentheses or quotes.

Example: typing '@cd mydir' (without the quotes) changes you working directory
to 'mydir', if it exists.

If you have 'automagic' enabled (via the command line option or with the
@automagic function), you don't need to type in the @ explicitly.

You can define your own magic functions to extend the system. See the supplied
ipythonrc and example-magic.py files for details (in your ipython
configuration directory, typically $HOME/.ipython/).

You can also define your own aliased names for magic functions. In your
ipythonrc file, placing a line like:

  execute __IP.magic_cl = __IP.magic_clear

will define @cl as a new name for @clear.

For a list of the available magic functions, use @lsmagic. For a description
of any of them, type @magic_name?.

Currently the magic system has the following functions:\n"""

        outmsg = ("%s\n%s\n\nSummary of magic functions (from @lsmagic):"
                  "\n\n@%s\n\n%s" % (outmsg,
                                     magic_docs,
                                     '  @'.join(self.lsmagic()),
                                     Magic.auto_status[self.rc.automagic] ) )

        page(outmsg,screen_lines=self.rc.screen_length)
  
    def magic_automagic(self, parameter_s = ''):
        """Make magic functions callable without having to type the initial @.
        
        Toggles on/off (when off, you must call it as @automagic, of
        course). Note that magic functions have lowest priority, so if there's
        a variable whose name collides with that of a magic fn, automagic
        won't work for that function (you get the variable instead). However,
        if you delete the variable (del var), the previously shadowed magic
        function becomes visible to automagic again."""
        
        self.rc.automagic = not self.rc.automagic
        print '\n' + Magic.auto_status[self.rc.automagic]

    def magic_autocall(self, parameter_s = ''):
        """Make functions callable without having to type parentheses.

        This toggles the autocall command line option on and off."""
        
        self.rc.autocall = not self.rc.autocall
        print "Automatic calling is:",['OFF','ON'][self.rc.autocall]

    def magic_hist(self, parameter_s = ''):
        """Print input history (_i<n> variables), with most recent last.
        
        @hist [-n]       -> print at most 40 inputs (some may be multi-line)\\
        @hist [-n] n     -> print at most n inputs\\
        @hist [-n] n1 n2 -> print inputs between n1 and n2 (n2 not included)\\

        Each input's number <n> is shown, and is accessible as the
        automatically generated variable _i<n>.  Multi-line statements are
        printed starting at a new line for easy copy/paste.

        If option -n is used, input numbers are not printed. This is useful if
        you want to get a printout of many lines which can be directly pasted
        into a text editor.

        This feature is only available if numbered prompts are in use."""

        if not self.do_full_cache:
            print 'This feature is only available if numbered prompts are in use.'
            return
        opts,args = self.parse_options(parameter_s,'n',mode='list')
        
        default_length = 40
        if len(args) == 0:
            final = self.outputcache.prompt_count
            init = max(1,final-default_length)
        elif len(args) == 1:
            final = self.outputcache.prompt_count
            init = max(1,final-int(args[0]))
        elif len(args) == 2:
            init,final = map(int,args)
        else:
            warn('@hist takes 0, 1 or 2 arguments separated by spaces.')
            print self.magic_hist.__doc__
            return
        width = len(str(final))
        line_sep = ['','\n']
        for in_num in range(init,final):
            #inline = eval('self.shell.user_ns["_i'+str(in_num)+'"]')
            inline = self.shell.user_ns['_ih'][in_num]
            multiline = inline.count('\n') > 1
            if not opts.has_key('n'):
                print str(in_num).ljust(width)+':'+ line_sep[multiline],
            if inline.startswith('#@') or inline.startswith('#!'):
                print inline[1:],
            else:
                print inline,


    def magic_p(self, parameter_s=''):
        """Just a short alias for Python's 'print'."""
        exec 'print ' + parameter_s in self.shell.user_ns


    def magic_r(self, parameter_s=''):
        """Repeat previous input.

        If given an argument, repeats the previous command which starts with
        the same string, otherwise it just repeats the previous input.

        Shell escaped commands (with ! as first character) are not recognized
        by this system, only pure python code and magic commands.
        """

        start = parameter_s.strip()
        # Identify magic commands even if automagic is on (which means
        # the in-memory version is different from that typed by the user).
        if self.shell.rc.automagic:
            start_magic = '@'+start
        else:
            start_magic = start
        # Look through the input history in reverse
        for n in range(len(self.shell.input_hist)-2,0,-1):
            input = self.shell.input_hist[n]
            if input.startswith('#@'):
                input = input[1:]
            if input != '@r\n' and \
               (input.startswith(start) or input.startswith(start_magic)):
                #print 'match',`input`  # dbg
                if input.startswith('@'):
                    input = magic2python(input)
                    #print 'modified',`input`  # dbg
                print 'Executing:',input,
                exec input in self.shell.user_ns
                return
        print 'No previous input matching `%s` found.' % start


    def magic_profile(self, parameter_s=''):
        """Print your currently active IPyhton profile."""
        if self.rc.profile:
            printpl('Current IPython profile: $self.rc.profile.')
        else:
            print 'No profile active.'
        
    def _inspect(self,meth,oname,**kw):
        """Generic interface to the inspector system.

        This function is meant to be called by pdef, pdoc & friends."""
        
        oname = oname.strip()
        info = Struct(self._ofind(oname))
        if info.found:
            pmethod = getattr(self.shell.inspector,meth)
            if meth == 'pdoc':
                formatter = info.ismagic and self.format_screen or None
                pmethod(info.obj,oname,formatter)
            elif meth == 'pinfo':
                formatter = info.ismagic and self.format_screen or None
                pmethod(info.obj,oname,info.namespace,formatter,
                        ismagic=info.ismagic,**kw)
            else:
                pmethod(info.obj,oname)
        else:
            print 'Object `%s` not found.' % oname
            return 'not found'  # so callers can take other action
        
    def magic_pdef(self, parameter_s=''):
        """Print the definition header for any callable object.

        If the object is a class, print the constructor information."""
        self._inspect('pdef',parameter_s)
        
    def magic_pdoc(self, parameter_s=''):
        """Print the docstring for an object.

        If the given object is a class, it will print both the class and the
        constructor docstrings."""
        self._inspect('pdoc',parameter_s)

    def magic_psource(self, parameter_s=''):
        """Print (or run through pager) the source code for an object."""
        self._inspect('psource',parameter_s)

    def magic_pfile(self, parameter_s=''):
        """Print (or run through pager) the file where an object is defined.

        The file opens at the line where the object definition begins. IPython
        will honor the environment variable PAGER if set, and otherwise will
        do its best to print the file in a convenient form.

        If the given argument is not an object currently defined, IPython will
        try to interpret it as a filename (automatically adding a .py extension
        if needed). You can thus use @pfile as a syntax highlighting code
        viewer."""

        # first interpret argument as an object name
        out = self._inspect('pfile',parameter_s)
        # if not, try the input as a filename
        if out == 'not found':
            try:
                filename = get_py_filename(parameter_s)
            except IOError,msg:
                print msg
                return
            page(self.shell.inspector.format(file(filename).read()))

            
    def magic_pinfo(self, parameter_s=''):
        """Provide detailed information about an object.

        '@pinfo object' is just a synonym for object? or ?object."""
        
        # look for the given object in all namespaces
        qmark1,oname,qmark2 = re.match('(\?*)([^?]*)(\??)',parameter_s).groups()
        # detail_level: 0 -> obj? , 1 -> obj??
        detail_level = 0
        if qmark1 or qmark2:
            detail_level = 1
        self._inspect('pinfo',oname,detail_level=detail_level)

    def magic_who_ls(self, parameter_s=''):
        """Return a list of all interactive variables."""
        out = []
        for i in self.shell.user_ns.keys():
            if not (i.startswith('_') or i.startswith('_i')) \
                   and not (self.internal_ns.has_key(i) or
                            self.user_config_ns.has_key(i)):
                out.append(i)
        # FIXME. The namespaces should be setup so that this kind of manual
        # kludges is unnecessary:
        if 'help' in out and \
           isinstance(self.shell.user_ns['help'],pydoc.Helper):
            out.remove('help')
        out.sort()
        return out
        
    def magic_who(self, parameter_s=''):
        """Print all interactive variables, with some minimal formatting.

        This excludes executed names loaded through your configuration
        file and things which are internal to IPython.

        This is deliberate, as typically you may load many modules and the
        purpose of @who is to show you only what you've manually defined."""

        varlist = self.magic_who_ls()
        if not varlist:
            print 'Interactive namespace is empty.'
            return

        # if we have variables, move on...

        # stupid flushing problem: when prompts have no separators, stdout is
        # getting lost. I'm starting to think this is a python bug. I'm having
        # to force a flush with a print because even a sys.stdout.flush
        # doesn't seem to do anything!
        
        for i in varlist:
            print i+'\t',
            sys.stdout.flush()  # FIXME. Why the hell isn't this flushing???
        print # well, this does force a flush at the expense of an extra \n

    def magic_whos(self, parameter_s=''):
        """Like @who, but gives some extra information about each variable.

        For all variables, the type is printed. Additionally it prints:\\
          - For {},[],(): their length.\\
          - Everything else: a string representation, snipping their middle if
          too long."""
        
        varnames = self.magic_who_ls()
        if not varnames:
            print 'Interactive namespace is empty.'
            return

        # if we have variables, move on...

        # for these types, show len() instead of data:
        seq_types = [types.DictType,types.ListType,types.TupleType]

        # Find all variable names and types so we can figure out column sizes
        get_vars = lambda i: self.locals[i]
        type_name = lambda v: type(v).__name__
        varlist = map(get_vars,varnames)
        typelist = map(type_name,varlist)
        # column labels and # of spaces as separator
        varlabel = 'Variable'
        typelabel = 'Type'
        datalabel = 'Data/Length'
        colsep = 3
        # find the size of the columns to format the output nicely
        varwidth = max(max(map(len,varnames)), len(varlabel)) + colsep
        typewidth = max(max(map(len,typelist)), len(typelabel)) + colsep
        # table header
        print varlabel.ljust(varwidth) + typelabel.ljust(typewidth) + \
              datalabel+'\n' + '-'*(varwidth+typewidth+len(datalabel))
        # and the table itself
        for vname,var,vtype in zip(varnames,varlist,typelist):
            print itpl("$vname.ljust(varwidth)$vtype.ljust(typewidth)"),
            if vtype in seq_types:
                print len(var)
            else:
                vstr = str(var)
                if len(vstr) < 50:
                    print vstr
                else:
                    printpl('$vstr[:20]<...>$vstr[-20:]')
                
    def magic_reset(self, parameter_s=''):
        """Resets the namespace by removing all names defined by the user.

        Input/Output history are left around in case you need them."""

        ans = raw_input(
          "Once deleted, variables cannot be recovered. Proceed (y/n)? ")
        if not ans.lower() == 'y':
            print 'Nothing done.'
            return
        for i in self.magic_who_ls():
            del(self.locals[i])

    def magic_config(self,parameter_s=''):
        """Show IPython's internal configuration."""
        
        page('Current configuration structure:\n'+
             pformat(self.rc.dict()))

    def magic_logstart(self,parameter_s=''):
        """Start logging anywhere in a session.

        @logstart [log_name [log_mode]]

        If no name is given, it defaults to a file named 'ipython.log' in your
        current directory, in 'rotate' mode (see below).

        '@logstart name' saves to file 'name' in 'backup' mode.  It saves your
        history up to that point and then continues logging.

        @logstart takes a second optional parameter: logging mode. This can be one
        of (note that the modes are given unquoted):\\
          over: overwrite existing log.\\
          backup: rename (if exists) to name~ and start name.\\
          append: well, that says it.\\
          rotate: create rotating logs name.1~, name.2~, etc.
        """

        #FIXME. This function should all be moved to the Logger class.
        
        valid_modes = qw('over backup append rotate')
        if self.LOG:
            print 'Logging is already in place. Logfile:',self.LOG
            return

        par = parameter_s.strip()
        if not par:
            logname = self.LOGDEF
            logmode = 'rotate'  # use rotate for the auto-generated logs
        else:
            try:
                logname,logmode = par.split()
            except:
                try:
                    logname = par
                    logmode = 'backup'
                except:
                    warn('Usage: @log [log_name [log_mode]]')
                    return
        if not logmode in valid_modes:
            warn('Logging NOT activated.\n'
                 'Usage: @log [log_name [log_mode]]\n'
                 'Valid modes: '+str(valid_modes))
            return

        # If we made it this far, I think we're ok:
        print 'Activating auto-logging.'
        print 'Current session state plus future input saved to:',logname
        print 'Logging mode: ',logmode
        # put logname into rc struct as if it had been called on the command line,
        # so it ends up saved in the log header
        old_logfile = self.rc.opts.get('logfile','')  # in case we need to restore it
        logname = os.path.expanduser(logname)
        self.rc.opts.logfile = logname
        self.LOGMODE = logmode  # FIXME: this should be set through a function.
        try:
            header = str(self.LOGHEAD)
            self.create_log(header,logname)
            self.logstart(header,logname)
        except:
            self.LOG = ''  # we are NOT logging, something went wrong
            self.rc.opts.logfile = old_logfile
            warn("Couldn't start log: "+str(sys.exc_info()[1]))
        else:  # log input history up to this point
            self.logfile.write(self.shell.user_ns['_ih'][1:])
            self.logfile.flush()
        
    def magic_logoff(self,parameter_s=''):
        """Temporarily stop logging.

        You must have previously started logging."""
        self.switch_log(0)
        
    def magic_logon(self,parameter_s=''):
        """Restart logging.

        This function is for restarting logging which you've temporarily
        stopped with @logoff. For starting logging for the first time, you
        must use the @logstart function, which allows you to specify an
        optional log filename."""
        
        self.switch_log(1)
    
    def magic_logstate(self,parameter_s=''):
        """Print the status of the logging system."""

        self.logstate()
        
    def magic_pdb(self, parameter_s=''):
        """Control the calling of the pdb interactive debugger.

        Call as '@pdb on', '@pdb 1', '@pdb off' or '@pdb 0'. If called without
        argument it works as a toggle.

        When an exception is triggered, IPython can optionally call the
        interactive pdb debugger after the traceback printout. @pdb toggles
        this feature on and off."""

        par = parameter_s.strip().lower()

        if par:
            try:
                pdb = {'off':0,'0':0,'on':1,'1':1}[par]
            except KeyError:
                print 'Incorrect argument. Use on/1, off/0 or nothing for a toggle.'
                return
            else:
               self.shell.InteractiveTB.call_pdb = pdb 
        else:
            self.shell.InteractiveTB.call_pdb = 1 - self.shell.InteractiveTB.call_pdb
        print 'Automatic pdb calling has been turned',\
              on_off(self.shell.InteractiveTB.call_pdb)

    def magic_prun(self, parameter_s ='',user_mode=1,
                   opts=None,arg_lst=None,prog_ns=None):

        """Run a statement through the python code profiler.

        Usage:\\
          @prun [options] statement

        The given statement (which doesn't require quote marks) is run via the
        python profiler in a manner similar to the profile.run() function.
        Namespaces are internally managed to work correctly; profile.run
        cannot be used in IPython because it makes certain assumptions about
        namespaces which do not hold under IPython.

        Options:

        -l <limit>: you can place restrictions on what or how much of the
        profile gets printed. The limit value can be:

          * A string: only information for function names containing this string
          is printed.

          * An integer: only these many lines are printed.

          * A float (between 0 and 1): this fraction of the report is printed
          (for example, use a limit of 0.4 to see the topmost 40% only).

        You can combine several limits with repeated use of the option. For
        example, '-l __init__ -l 5' will print only the topmost 5 lines of
        information about class constructors.

        -r: return the pstats.Stats object generated by the profiling. This
        object has all the information about the profile in it, and you can
        later use it for further analysis or in other functions.

        Since magic functions have a particular form of calling which prevents
        you from writing something like:\\
          In [1]: p = @prun -r print 4  # invalid!\\
        you must instead use IPython's automatic variables to assign this:\\
          In [1]: @prun -r print 4  \\
          Out[1]: <pstats.Stats instance at 0x8222cec>\\
          In [2]: stats = _

        If you really need to assign this value via an explicit function call,
        you can always tap directly into the true name of the magic function
        with:\\
          In [3]: stats = __IP.magic_prun('-r print 4')

       -s <key>: sort profile by given key. You can provide more than one key
        by using the option several times: '-s key1 -s key2 -s key3...'. The
        default sorting key is 'stdname'.

        The following is copied verbatim from the profile documentation
        referenced below:

        When more than one key is provided, additional keys are used as
        secondary criteria when the there is equality in all keys selected
        before them.
        
        Abbreviations can be used for any key names, as long as the
        abbreviation is unambiguous.  The following are the keys currently
        defined:

                Valid Arg       Meaning\\
                  "calls"      call count\\
                  "cumulative" cumulative time\\
                  "file"       file name\\
                  "module"     file name\\
                  "pcalls"     primitive call count\\
                  "line"       line number\\
                  "name"       function name\\
                  "nfl"        name/file/line\\
                  "stdname"    standard name\\
                  "time"       internal time

        Note that all sorts on statistics are in descending order (placing
        most time consuming items first), where as name, file, and line number
        searches are in ascending order (i.e., alphabetical). The subtle
        distinction between "nfl" and "stdname" is that the standard name is a
        sort of the name as printed, which means that the embedded line
        numbers get compared in an odd way.  For example, lines 3, 20, and 40
        would (if the file names were the same) appear in the string order
        "20" "3" and "40".  In contrast, "nfl" does a numeric compare of the
        line numbers.  In fact, sort_stats("nfl") is the same as
        sort_stats("name", "file", "line").

        -t <filename>: save profile results as shown on screen to a text
        file. The profile is still shown on screen.

        -d <filename>: save (via dump_stats) profile statistics to given
        filename. This data is in a format understod by the pstats module, and
        is generated by a call to the dump_stats() method of profile
        objects. The profile is still shown on screen.

        If you want to run complete programs under the profiler's control, use
        '@run -p [opts] filename.py [args to program]' and then any profile
        specific options as described here.
        
        You can read the complete documentation for the profile module with:
          In [1]: import profile; profile.help() """

        opts_def = Struct(d=[''],l=[],s=['stdname'],t=[''])
        if user_mode:  # regular user call
            opts,arg_str = self.parse_options(parameter_s,'d:l:rs:t:',
                                              list_all=1)
            namespace = self.shell.user_ns
        else:  # called to run a program by @run -p
            try:
                filename = get_py_filename(arg_lst[0])
            except IOError,msg:
                warn(msg)
                return

            arg_str = 'execfile(filename,prog_ns)'
            namespace = locals()

        opts.merge(opts_def)
        
        prof = Profile()
        try:
            prof = prof.runctx(arg_str,namespace,namespace)
            sys_exit = ''
        except SystemExit:
            sys_exit = """*** SystemExit exception caught in code being profiled."""

        stats = pstats.Stats(prof).strip_dirs().sort_stats(*opts.s)

        lims = opts.l
        if lims:
            lims = []  # rebuild lims with ints/floats/strings
            for lim in opts.l:
                try:
                    lims.append(int(lim))
                except ValueError:
                    try:
                        lims.append(float(lim))
                    except ValueError:
                        lims.append(lim)
                    
        # trap output
        sys_stdout = sys.stdout
        stdout_trap = StringIO()
        try:
            sys.stdout = stdout_trap
            stats.print_stats(*lims)
        finally:
            sys.stdout = sys_stdout
        output = stdout_trap.getvalue()
        output = output.rstrip()

        page(output,screen_lines=self.rc.screen_length)
        print sys_exit,

        dump_file = opts.d[0]
        text_file = opts.t[0]
        if dump_file:
            prof.dump_stats(dump_file)
            print '\n*** Profile stats marshalled to file',\
                  `dump_file`+'.',sys_exit
        if text_file:
            file(text_file,'w').write(output)
            print '\n*** Profile printout saved to text file',\
                  `text_file`+'.',sys_exit

        if opts.has_key('r'):
            return stats
        else:
            return None


    def magic_run(self, parameter_s =''):
        """Run the named file inside IPython as a program.

        Usage:\\
          @run [-n -i -p [profile options]] file [args]

        Parameters after the filename are passed as command-line arguments to
        the program (put in sys.argv). Then, control returns to IPython's
        prompt.

        This is similar to running at a system prompt:\\
          $ python file args\\
        but has the advantage of giving you IPython's tracebacks, and of
        loading all variables into your interactive namespace for further use
        (unless -p is used, see below).

        The file is executed in a namespace initially consisting only of
        __name__=='__main__' and sys.argv constructed as indicated. It thus
        sees its environment as if it were being run as a stand-alone
        program. But after execution, the IPython interactive namespace gets
        updated with all variables defined in the program (except for __name__
        and sys.argv). This allows for very convenient loading of code for
        interactive work, while giving each program a 'clean sheet' to run in.

        Options:
        
        -n: __name__ is NOT set to '__main__', but to the running file's name
        without extension (as python does under import).  This allows running
        scripts and reloading the definitions in them without calling code
        protected by an ' if __name__ == "__main__" ' clause.

        -i: run the file in IPython's namespace instead of an empty one. This
        is useful if you are experimenting with code written in a text editor
        which depends on variables defined interactively.

        -p: run program under the control of the Python profiler module (which
        prints a detailed report of execution times, function calls, etc).

        You can pass other options after -p which affect the behavior of the
        profiler itself. See the docs for @prun for details.

        In this mode, the program's variables do NOT propagate back to the
        IPython interactive namespace (because they remain in the namespace
        where the profiler executes them).

        Internally this triggers a call to @prun, see its documentation for
        details on the options available specifically for profiling."""

        # get arguments and set sys.argv for program to be run.
        opts,arg_lst = self.parse_options(parameter_s,'nipd:l:rs:t:',
                                          mode='list',list_all=1)

        try:
            filename = get_py_filename(arg_lst[0])
        except IndexError:
            warn('you must provide at least a filename.')
            print '\n@run:\n',inspect.getdoc(self.magic_run)
            return
        except IOError,msg:
            warn(msg)
            return

        save_argv = sys.argv # save it for later restoring
        # perform shell-like expansions on the argument list before passing it
        # to programs
        xvars = os.path.expandvars
        xuser = os.path.expanduser
        xpand = lambda s: xvars(xuser(s))
        sys.argv = [xpand(arg) for arg in arg_lst] 

        if opts.has_key('i'):
            prog_ns = self.shell.user_ns
            __name__save = self.shell.user_ns['__name__']
            prog_ns['__name__'] = '__main__'
        else:
            if opts.has_key('n'):
                name = os.path.splitext(os.path.basename(filename))[0]
            else:
                name = '__main__'
            prog_ns = {'__name__':name}

        # pickle fix.  See iplib for an explanation
        sys.modules[prog_ns['__name__']] = FakeModule(prog_ns)
        
        stats = None
        try:
            if opts.has_key('p'):
                #cmd = parameter_s.split()[:-1] # FIXME: dead code?
                stats = self.magic_prun('',0,opts,arg_lst,prog_ns)
            else:
                self.shell.safe_execfile(filename,prog_ns,prog_ns)
                if opts.has_key('i'):
                    self.shell.user_ns['__name__'] = __name__save
                else:
                    # update IPython interactive namespace
                    del prog_ns['__name__']
                    self.shell.user_ns.update(prog_ns)
        finally:
            sys.argv = save_argv
        return stats

    def magic_runlog(self, parameter_s =''):
        """Run files as logs.

        Usage:\\
          @runlog file1 file2 ...

        Run the named files (treating them as log files) in sequence inside
        the interpreter, and return to the prompt.  This is much slower than
        @run because each line is executed in a try/except block, but it
        allows running files with syntax errors in them.

        Normally IPython will guess when a file is one of its own logfiles, so
        you can typically use @run even for logs. This shorthand allows you to
        force any file to be treated as a log file."""

        for f in parameter_s.split():
            self.shell.safe_execfile(f,self.shell.user_ns,self.shell.user_ns,islog=1)

    def magic_macro(self,parameter_s = ''):
        """Define a set of input lines as a macro for future re-execution.

        Usage:\\
          @macro name n1:n2 n3:n4 ... n5 .. n6 ...

        This will define a global variable called `name` which is a string
        made of joining the slices and lines you specify (n1,n2,... numbers
        above) from your input history into a single string. This variable
        acts like an automatic function which re-executes those lines as if
        you had typed them. You just type 'name' at the prompt and the code
        executes.

        Note that the slices use the standard Python slicing notation (5:8
        means include lines numbered 5,6,7).

        For example, if your history contains (@hist prints it):
        
          44: x=1\\
          45: y=3\\
          46: z=x+y\\
          47: print x\\
          48: a=5\\
          49: print 'x',x,'y',y\\

        you can create a macro with lines 44 through 47 (included) and line 49
        called my_macro with:

          In [51]: @macro my_macro 44:48 49

        Now, typing `my_macro` (without quotes) will re-execute all this code
        in one pass.

        You don't need to give the line-numbers in order, and any given line
        number can appear multiple times. You can assemble macros with any
        lines from your input history in any order.

        The macro is a simple object which holds its value in an attribute,
        but IPython's display system checks for macros and executes them as
        code instead of printing them when you type their name.

        You can view a macro's contents by explicitly printing it with:
        
          'print macro_name'.

        For one-off cases which DON'T contain magic function calls in them you
        can obtain similar results by explicitly executing slices from your
        input history with:

          In [60]: exec In[44:48]+In[49]"""

        args = parameter_s.split()
        name,ranges = args[0], args[1:]
        #print 'rng',ranges  # dbg
        cmds = self.extract_input_slices(ranges)
        macro = Macro(cmds)
        self.shell.user_ns.update({name:macro})
        print 'Macro `%s` created. To execute, type its name (without quotes).' % name
        print 'Macro contents:'
        print str(macro).rstrip(),

    def magic_save(self,parameter_s = ''):
        """Save a set of lines to a given filename.

        Usage:\\
          @save filename n1:n2 n3:n4 ... n5 .. n6 ...

        This function uses the same syntax as @macro for line extraction, but
        instead of creating a macro it saves the resulting string to the
        filename you specify.

        It adds a '.py' extension to the file if you don't do so yourself, and
        it asks for confirmation before overwriting existing files."""

        args = parameter_s.split()
        fname,ranges = args[0], args[1:]
        if not fname.endswith('.py'):
            fname += '.py'
        if os.path.isfile(fname):
            ans = raw_input('File `%s` exists. Overwrite (y/[N])? ' % fname)
            if ans.lower() not in ['y','yes']:
                print 'Operation cancelled.'
                return
        cmds = ''.join(self.extract_input_slices(ranges))
        f = file(fname,'w')
        f.write(cmds)
        f.close()
        print 'The following commands were written to file `%s`:' % fname
        print cmds

    def magic_ed(self,parameter_s = ''):
        """Alias to @edit."""
        return self.magic_edit(parameter_s)

    def magic_edit(self,parameter_s = '',last_call=['','']):
        """Bring up an editor and execute the resulting code.

        Usage:
          @edit [options] [args]

        @edit will use the editor you have configured in your environment as
        the EDITOR variable. If this isn't found, it will default to vi under
        Linux/Unix and to notepad under Windows.

        You can also set the value of this editor via the commmand-line option
        '-editor' or in your ipythonrc file. This is useful if you wish to use
        specifically for IPython an editor different from your typical default
        (and for Windows users who typically don't set environment variables).

        This command allows you to conveniently edit multi-line code right in
        your IPython session.
        
        If called without arguments, @edit opens up an empty editor with a
        temporary file and will execute the contents of this file (don't
        forget to save it!) when you close it.

        Options:

        -p: this will call the editor with the same data as the previous time
        it was used, regardless of how long ago (in your current session) it
        was.

        -x: do not execute the edited code immediately upon exit. This is
        mainly useful if you are editing programs which need to be called with
        command line arguments, which you can then do using @run.

        Arguments:

        If arguments are given, the following possibilites exist:

        - The arguments are numbers or pairs of colon-separated numbers (like
        1 4:8 9). These are interpreted as lines of previous input to be
        loaded into the editor. The syntax is the same of the @macro command.

        - If the argument doesn't start with a number, it is evaluated as a
        variable and its contents loaded into the editor. You can thus edit
        any string which contains python code (including the result of
        previous edits).

        - If the argument is the name of an object (other than a string),
        IPython will try to locate the file where it was defined and open the
        editor at the point where it is defined. You can use `@edit function`
        to load an editor exactly at the point where 'function' is defined,
        edit it and have the file be executed automatically.

        Note: opening at an exact line is only supported under Unix, and some
        editors (like kedit and gedit) do not understand the '+NUMBER'
        parameter necessary for this feature. Good editors like (X)Emacs, vi,
        jed, pico and joe all do.

        - If the argument is not found as a variable, IPython will look for a
        file with that name (adding .py if necessary) and load it into the
        editor. It will execute its contents with execfile() when you exit,
        loading any code in the file into your interactive namespace.

        After executing your code, @edit will return as output the code you
        typed in the editor (except when it was an existing file). This way
        you can reload the code in further invocations of @edit as a variable,
        via _<NUMBER> or Out[<NUMBER>], where <NUMBER> is the prompt number of
        the output.

        Note that @edit is also available through the alias @ed.

        This is an example of creating a simple function inside the editor and
        then modifying it. First, start up the editor:

        In [1]: ed\\
        Editing... done. Executing edited code...\\
        Out[1]: 'def foo():\n    print "foo() was defined in an editing session"\n'\\

        We can then call the function foo():
        In [2]: foo()
        foo() was defined in an editing session

        Now we edit foo.  IPython automatically loads the editor with the
        (temporary) file where foo() was previously defined.
        In [3]: ed foo
        Editing... done. Executing edited code...

        And if we call foo() again we get the modified version:
        In [4]: foo()
        foo() has now been changed!

        Here is an example of how to edit a code snippet successive
        times. First we call the editor:

        In [8]: ed\\
        Editing... done. Executing edited code...\\
        hello\\
        Out[8]: "print 'hello'\\n"\\

        Now we call it again with the previous output (stored in _):

        In [9]: ed _\\
        Editing... done. Executing edited code...\\
        hello world\\
        Out[9]: "print 'hello world'\\n"\\

        Now we call it with the output #8 (stored in _8, also as Out[8]):

        In [10]: ed _8\\
        Editing... done. Executing edited code...\\
        hello again\\
        Out[10]: "print 'hello again'\\n"
        """

        opts,args = self.parse_options(parameter_s,'px')

        if opts.has_key('p'):
            args = '_%s' % last_call[0]
            if not self.shell.user_ns.has_key(args):
                args = last_call[1]
        # use last_call to remember the state of the previous call, but don't
        # let it be clobbered by successive '-p' calls.
        try:
            last_call[0] = self.shell.outputcache.prompt_count
            if not opts.has_key('p'):
                last_call[1] = parameter_s
        except:
            pass

        # by default this is done with temp files, except when the given
        # arg is a filename
        use_temp = 1
        # marker for at which line to open the file (for existing objects)
        linemark = ''

        if re.match(r'\d',args):
            # Mode where user specifies ranges of lines, like in @macro.
            # This means that you can't edit files whose names begin with
            # numbers this way. Tough.
            ranges = args.split()
            data = ''.join(self.extract_input_slices(ranges))
        elif args:
            try:
                # Load the parameter given as a variable. If not a string,
                # process it as an object instead (below)
                data = eval(args,self.shell.user_ns)
                if not type(data) in StringTypes:
                    raise 'data is an object'
            except (NameError,SyntaxError):
                # given argument is not a variable, try as a filename
                try:
                    filename = get_py_filename(args)
                except IOError:
                    if args.endswith('.py'):
                        filename = args
                    else:
                        warn("Argument given (%s) can't be found as a variable "
                             "or as a filename." % args)
                        return
                data = ''
                use_temp = 0
            except 'data is an object':
                # For objects, try to edit the file where they are defined
                try:
                    filename = inspect.getabsfile(data)
                except TypeError:
                    warn('Could not find file where `%s` is defined.' % args)
                    return
                # Now, make sure we can actually read the source (if it was in
                # a temp file it's gone by now).
                try:
                    lineno = inspect.getsourcelines(data)[1]
                except IOError:
                    warn('The file `%s` where `%s` was defined cannot be read.'
                         % (filename,data))
                    return
                # Decent Unix editors know how to start at a given line
                if os.name == 'posix':
                    linemark = '+%s' % lineno
                use_temp = 0
        else:
            data = ''

        if use_temp:
            filename = tempfile.mktemp('.py')
            self.shell.tempfiles.append(filename)
        
        if data and use_temp:
            tmp_file = open(filename,'w')
            tmp_file.write(data)
            tmp_file.close()

        # do actual editing here
        print 'Editing...',
        sys.stdout.flush()
        xsys('%s %s %s' % (self.shell.rc.editor,linemark,filename))
        if opts.has_key('x'):  # -x prevents actual execution
            print
        else:
            print 'done. Executing edited code...'
            try:
                execfile(filename,self.shell.user_ns)
            except IOError:
                warn('File not found. Did you forget to save?')
                return
        if use_temp:
            contents = open(filename).read()
            return contents

    def magic_xmode(self,parameter_s = ''):
        """Switch modes for the exception handlers.

        Valid modes: Plain, Context and Verbose.

        If called without arguments, acts as a toggle."""

        new_mode = parameter_s.strip().capitalize()
        try:
            self.InteractiveTB.set_mode(mode = new_mode)
            print 'Exception reporting mode:',self.InteractiveTB.mode
        except:
            warn('Error changing exception modes.\n' + str(sys.exc_info()[1]))
            
    def magic_colors(self,parameter_s = ''):
        """Switch color scheme for the prompts and exception handlers.

        Currently implemented schemes: NoColor, Linux, LightBG.

        Color scheme names are not case-sensitive."""
        
        new_scheme = parameter_s.strip()
        if not new_scheme:
            print 'You must specify a color scheme.'
            return
        try:
            self.shell.outputcache.set_colors(new_scheme)
        except:
            warn('Error changing prompt color schemes.\n'
                 + str(sys.exc_info()[1]))
        else:
            self.shell.rc.colors = \
                       self.shell.outputcache.color_table.active_scheme_name
        try:
            self.shell.InteractiveTB.set_colors(scheme = new_scheme)
            self.shell.SyntaxTB.set_colors(scheme = new_scheme)
        except:
            warn('Error changing exception color schemes.\n'
                 + str(sys.exc_info()[1]))
        if self.shell.rc.color_info:
            try:
                self.shell.inspector.set_active_scheme(new_scheme)
            except:
                warn('Error changing object inspector color schemes.\n'
                     + str(sys.exc_info()[1]))
        else:
            self.shell.inspector.set_active_scheme('NoColor')
                
    def magic_color_info(self,parameter_s = ''):
        """Toggle color_info.

        The color_info configuration parameter controls whether colors are
        used for displaying object details (by things like @psource, @pfile or
        the '?' system). This function toggles this value with each call.

        Note that unless you have a fairly recent pager (less works better
        than more) in your system, using colored object information displays
        will not work properly. Test it and see."""
        
        self.shell.rc.color_info = 1 - self.shell.rc.color_info
        self.magic_colors(self.shell.rc.colors)
        print 'Object introspection functions have now coloring:',
        print ['OFF','ON'][self.shell.rc.color_info]

    def magic_Pprint(self, parameter_s=''):
        """Toggle pretty printing on/off."""
        
        self.shell.outputcache.Pprint = 1 - self.shell.outputcache.Pprint
        print 'Pretty printing has been turned', \
              ['OFF','ON'][self.shell.outputcache.Pprint]
        
    def magic_Exit(self, parameter_s=''):
        """Exit IPython without confirmation."""

        raise SystemExit,'IPythonExit'

    def magic_Quit(self, parameter_s=''):
        """Exit IPython without confirmation (like @Exit)."""

        raise SystemExit,'IPythonExit'
        
    #......................................................................
    # Functions to implement unix shell-type things

    # Cool trick using Python's dynamic features:
    # @alias dynamically generates new functions as requested.
    def magic_alias(self, parameter_s = ''):
        """Define an alias for a system command.

        '@alias alias_name cmd' defines 'alias_name' as an alias for 'cmd'

        Then, typing '@alias_name params' will execute the system command 'cmd
        params' (from your underlying operating system).

        You can also define aliases with parameters using %s specifiers (one
        per parameter):
        
          In [1]: alias parts echo first %s second %s\\
          In [2]: @parts A B\\
          first A second B\\
          In [3]: @parts A\\
          Incorrect number of arguments: 2 expected.\\
          parts is an alias to: 'echo first %s second %s'\\

        If called with no parameters, @alias prints the current alias table."""

        par = parameter_s.strip()
        if not par:
            if self.rc.automagic:
                prechar = ''
            else:
                prechar = '@'
            print 'Alias\t\tSystem Command\n'+'-'*30
            aliases = self.alias_table.keys()
            aliases.sort()
            for alias in aliases:
                print prechar+alias+'\t\t'+self.alias_table[alias]
            return
        try:
            alias,cmd = par.split(' ',1)
        except:
            print inspect.getdoc(self.magic_alias)
            return
        nargs = cmd.count('%s')
        if nargs == 0:  # simple aliases
            fndef = itpl(
"""
def magic_${alias}(parameter_s = ''):
    '''Alias to the system command '$cmd' '''
    xsys('$cmd '+str(parameter_s))

self.magic_$alias = magic_$alias
""")
        else:  # parametric aliases
            fndef = itpl(
"""
def magic_${alias}(parameter_s = ''):
    '''Alias to the system command '$cmd' '''
    cmd = '$cmd'
    nargs = cmd.count('%s')
    args = str(parameter_s).split()

    if len(args) != nargs:
        print 'Incorrect number of arguments:',nargs,'expected.'
        print "$alias is an alias to: '$cmd'"
        return
    else:
        cmd_call = cmd % tuple(args)
        xsys(cmd_call)

self.magic_$alias = magic_$alias
""")
        try:
            exec fndef in globals(),locals()
        except:
            print self.magic_alias.__doc__
        self.alias_table.update({alias:cmd})
    # end magic_alias
        
    def magic_pwd(self, parameter_s = ''):
        """Return the current working directory path."""
        return os.getcwd()

    if os.name == 'posix':
        def magic_lf(self, parameter_s=''):
            """List (in color) things which are normal files."""
            self.magic_lc(parameter_s+' | grep ^-')

        def magic_ll(self, parameter_s=''):
            """List (in color) things which are symbolic links."""
            self.magic_lc(parameter_s+' | grep ^l')

        def magic_ld(self, parameter_s=''):
            """List (in color) things which are directories or links to directories."""
            self.magic_lc(parameter_s+' | grep /$')

        def magic_lx(self, parameter_s=''):
            """List (in color) things which are executable."""
            self.magic_lc(parameter_s+'| grep ^-..x')

    def magic_cd(self, parameter_s=''):
        """Change the current working directory.

        This command automatically maintains an internal list of directories
        you visit during your IPython session, in the variable _dh. The
        command @dhist shows this history nicely formatted.

        cd -<n> changes to the n-th directory in the directory history.

        cd - changes to the last visited directory.

        Note that !cd doesn't work for this purpose because the shell where
        !command runs is immediately discarded after executing 'command'."""
        
        ps = parameter_s.strip()
        if ps == '-':
            try:
                ps = self.shell.user_ns['_dh'][-2]
            except:
                print 'No previous directory to change to.'
                return
        elif ps.startswith('-'):
            try:
                ps = self.shell.user_ns['_dh'][
                    int(ps.replace('-','').strip())]
            except:
                print 'Requested directory doesn not exist in history.'
                return
        if ps:
            try:
                os.chdir(os.path.expanduser(ps))
            except OSError:
                print sys.exc_info()[1]
            else:
                self.shell.user_ns['_dh'].append(os.getcwd())
                
        else:
            os.chdir(self.home_dir)
            self.shell.user_ns['_dh'].append(os.getcwd())
        print self.shell.user_ns['_dh'][-1]

    def magic_dhist(self, parameter_s=''):
        """Print your history of visited directories.

        @dhist       -> print full history\\
        @dhist n     -> print last n entries only\\
        @dhist n1 n2 -> print entries between n1 and n2 (n1 not included)\\

        This history is automatically maintained by the @cd command, and
        always available as the global list variable _dh. You can use @cd -<n>
        to go to directory number <n>."""

        dh = self.shell.user_ns['_dh']
        if parameter_s:
            try:
                args = map(int,parameter_s.split())
            except:
                self.arg_err(Magic.magic_dhist)
                return
            if len(args) == 1:
                ini,fin = max(len(dh)-(args[0]),0),len(dh)
            elif len(args) == 2:
                ini,fin = args
            else:
                self.arg_err(Magic.magic_dhist)
                return
        else:
            ini,fin = 0,len(dh)
        nlprint(dh,
                header = 'Directory history (kept in _dh)',
                start=ini,stop=fin)

    def magic_env(self, parameter_s=''):
        """List environment variables."""
        
        # environ is an instance of UserDict
        return os.environ.data

    def magic_pushd(self, parameter_s=''):
        """Place the current dir on stack and change directory.
        
        Usage:\\
          @pushd ['dirname']

        @pushd with no arguments does a @pushd to your home directory.
        """
        if parameter_s == '': parameter_s = '~'
        if len(self.dir_stack)>0 and os.path.expanduser(parameter_s) != \
           os.path.expanduser(self.dir_stack[0]):
            try:
                self.magic_cd(parameter_s)
                self.dir_stack.insert(0,os.getcwd().replace(self.home_dir,'~'))
                self.magic_dirs()
            except:
                print 'Invalid directory'
        else:
            print 'You are already there!'

    def magic_popd(self, parameter_s=''):
        """Change to directory popped off the top of the stack.
        """
        if len (self.dir_stack) > 1:
            self.dir_stack.pop(0)
            self.magic_cd(self.dir_stack[0])
            print self.dir_stack[0]
        else:
            print "You can't remove the starting directory from the stack:",\
                  self.dir_stack

    def magic_dirs(self, parameter_s=''):
        """Return the current directory stack."""

        return self.dir_stack[:]
# end Magic
