# -*- coding: iso-8859-1 -*-
"""
IPython -- An enhanced Interactive Python

Requires Python 2.1 or newer.

This file contains all the classes and helper functions specific to IPython.

$Id$
"""

from __future__ import nested_scopes

#*****************************************************************************
#       Copyright (C) 2001 Janko Hauser <jh@comunit.de> and
#                          Fernando Perez <fperez@colorado.edu>
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
#
#
# Note: this code originally subclassed code.InteractiveConsole from the
# Python standard library.  Over time, much of that class has been copied
# verbatim here for modifications which could not be accomplished by
# subclassing.  The Python License (sec. 2) allows for this, but it's always
# nice to acknowledge credit where credit is due.
#
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
import __main__
import __builtin__
import exceptions
import keyword
import os, sys, shutil
import code, glob, types, re
import string, StringIO
import inspect, pydoc
import bdb, pdb
import UserList # don't subclass list so this works with Python2.1
from pprint import pprint, pformat
import cPickle as pickle
import traceback

# Homebrewed modules
import OInspect,PyColorize
import ultraTB
from ultraTB import ColorScheme,ColorSchemeTable  # too long names
from Logger import Logger
from Magic import Magic,magic2python,shlex_split
from usage import cmd_line_usage,interactive_usage
from Struct import Struct
from Itpl import Itpl,itpl,printpl,ItplNS,itplns
from FakeModule import FakeModule
from genutils import *

#****************************************************************************
# Some utility function definitions
def import_fail_info(mod_name,fns=None):
    """Inform load failure for a module."""

    if fns == None:
        warn("Loading of %s failed.\n" % (mod_name,))
    else:
        warn("Loading of %s from %s failed.\n" % (fns,mod_name))

def qw_lol(indata):
    """qw_lol('a b') -> [['a','b']],
    otherwise it's just a call to qw().

    We need this to make sure the modules_some keys *always* end up as a
    list of lists."""

    if type(indata) in StringTypes:
        return [qw(indata)]
    else:
        return qw(indata)

#-----------------------------------------------------------------------------
# Local use classes
try:
    import FlexCompleter

    class MagicCompleter(FlexCompleter.Completer):
        """Extension of the completer class to work on @-prefixed lines."""

        def __init__(self, namespace = None, omit__names = 0,alias_table=None):
            """MagicCompleter(namespace = None, omit__names = 0) -> completer

            Return a completer object suitable for use by the readline library
            via readline.set_completer().

            The optional omit__names parameter sets the completer to omit the
            'magic' names (__magicname__) for python objects unless the text
            to be completed explicitly starts with one or more underscores.

            If alias_table is supplied, it should be a dictionary of aliases
            to complete. """

            FlexCompleter.Completer.__init__(self,namespace)
            self.readline = FlexCompleter.readline
            delims = self.readline.get_completer_delims()
            delims = delims.replace('@','')
            self.readline.set_completer_delims(delims)
            self.get_line_buffer = self.readline.get_line_buffer
            self.omit__names = omit__names
            if alias_table is None:
                alias_table = {}
            self.alias_table = alias_table
            # Regexp to split filenames with spaces in them
            self.space_name_re = re.compile(r'([^\\] )')
            # Hold a local ref. to glob.glob for speed
            self.glob = glob.glob
            # Special handling of backslashes needed in win32 platforms
            if sys.platform == "win32":
                self.clean_glob = self._clean_glob_win32
            else:
                self.clean_glob = self._clean_glob
            self.matchers = ['python_matches','file_matches','alias_matches']

        # Code contributed by Alex Schmolck, for ipython/emacs integration
        def all_completions(self, text):
            """Return all possible completions for the benefit of emacs."""
            
            completions = []
            try:
                for i in xrange(sys.maxint):
                    res = self.complete(text, i)

                    if not res: break

                    completions.append(res)
            #XXX workaround for ``notDefined.<tab>``
            except NameError:
                pass
            return completions
        # /end Alex Schmolck code.

        def _clean_glob(self,text):
            return self.glob("%s*" % text)
            
        def _clean_glob_win32(self,text):
            return [f.replace("\\","/")
                    for f in self.glob("%s*" % text)]            

        def file_matches(self, text, state):
            """Match filneames, expanding ~USER type strings.

            Most of the seemingly convoluted logic in this completer is an
            attempt to handle filenames with spaces in them.  And yet it's not
            quite perfect, because Python's readline doesn't expose all of the
            GNU readline details needed for this to be done correctly.

            For a filename with a space in it, the printed completions will be
            only the parts after what's already been typed (instead of the
            full completions, as is normally done).  I don't think with the
            current (as of Python 2.3) Python readline it's possible to do
            better."""
            
            #print 'Completer->file_matches: <%s>, state:%s' % (text,state) # dbg

            # chars that require escaping with backslash - i.e. chars
            # that readline treats incorrectly as delimiters, but we
            # don't want to treat as delimiters in filename matching
            # when escaped with backslash
            
            protectables = ' ()[]{}'

            def protect_filename(s):
                return "".join([(ch in protectables and '\\' + ch or ch) for ch in s])

            lbuf = self.get_line_buffer()[:self.readline.get_endidx()]
            try:
                lsplit = shlex_split(lbuf)[-1]
            except ValueError:
                # unmatched ", or backslash without escaped character typically
                return None   
            except IndexError:
                # tab pressed on empty line
                lsplit = ""
                
            if lsplit != protect_filename(lsplit):
                # if protectables are found, do matching on the whole escaped name
                has_protectables = 1
                text0,text = text,lsplit
            else:
                has_protectables = 0
                text = os.path.expanduser(text)
            
            if text == "":
                return [protect_filename(f) for f in self.glob("*")]

            m0 = self.clean_glob(text.replace('\\',''))
            if has_protectables:
                # If we had protectables, we need to revert our
                # changes to the beginning of filename so that we
                # don't double-write the part of the filename we have
                # so far
                len_lsplit = len(lsplit)
                matches = [text0 + protect_filename(f[len_lsplit:]) for f in m0]
            else:
                matches = [protect_filename(f) for f in m0]
            if len(matches) == 1:
                if os.path.isdir(matches[0]):
                    # Takes care of links to directories also.  Use '/' explicitly,
                    # even under Windows, so that name completions don't end up
                    # escaped.
                    matches[0] += '/'
            return matches

        def alias_matches(self, text, state):
            """Match internal system aliases"""
            #print 'Completer->alias_matches:',text # dbg
            text = os.path.expanduser(text)
            aliases =  self.alias_table.keys()
            if text == "":
                return aliases
            else:
                return [alias for alias in aliases if alias.startswith(text)]
            
        def python_matches(self,text,state):
            """Match attributes or global python names"""
            #print 'Completer->python_matches' # dbg
            if "." in text:
                try:
                    matches = self.attr_matches(text)
                    if text.endswith('.') and self.omit__names:
                        # true if txt is _not_ a __ name, false otherwise:
                        no__name = (lambda txt:
                                    re.match(r'.*\.__.*?__',txt) is None)
                        matches = filter(no__name, matches)
                except NameError:
                    # catches <undefined attributes>.<tab>
                    matches = []
            else:
                matches = self.global_matches(text)
                # this is so completion finds magics when automagic is on:
                if matches == [] and not text.startswith(os.sep):
                    matches = self.attr_matches('__IP.magic_'+text)
            return matches

        def complete(self, text, state):
            """Return the next possible completion for 'text'.

            This is called successively with state == 0, 1, 2, ... until it
            returns None.  The completion should begin with 'text'.  """
            
            #print '\n*** COMPLETE: <%s>' % text  # dbg
            try:
                if text.startswith('@'):
                    text = text.replace('@','__IP.magic_')
                if text.startswith('~'):
                    text = os.path.expanduser(text)
                if state == 0:
                    for matcher in self.matchers:
                        #print 'Calling matcher:',matcher # dbg
                        self.matches = getattr(self,matcher)(text,state)
                        if self.matches:
                            break
                try:
                    return self.matches[state].replace('__IP.magic_','@')
                except IndexError:
                    return None
            except SyntaxError:
                pass
            except:
                # needed because readline doesn't deal with exceptions
                # properly (just beeps and ignores)
                print "\nCompletion attempt raised an exception!"
                traceback.print_exc()
                

except ImportError:
    pass  # no readline support

except KeyError:
    pass  # Windows doesn't set TERM, it doesn't matter


class InputList(UserList.UserList):
    """Class to store user input.

    It's basically a list, but slices return a string instead of a list, thus
    allowing things like (assuming 'In' is an instance):

    exec In[4:7]

    or

    exec In[5:9] + In[14] + In[21:25]"""

    def __getslice__(self,i,j):
        return ''.join(UserList.UserList.__getslice__(self,i,j))

#****************************************************************************
# Local use exceptions
class SpaceInInput(exceptions.Exception):
    pass

#****************************************************************************
# Main IPython class

class InteractiveShell(code.InteractiveConsole, Logger, Magic):
    """An enhanced console for Python."""

    def __init__(self,name,usage=None,rc=Struct(opts=None,args=None),
                 user_ns = None):

        # Put a reference to self in builtins so that any form of embedded or
        # imported code can test for being inside IPython.
        __builtin__.__IPYTHON__ = self

        # Keep in the builtins a flag for when IPython is active.  We set it
        # with setdefault so that multiple nested IPythons don't clobber one
        # another.  Each will increase its value by one upon being activated,
        # which also gives us a way to determine the nesting level.
        __builtin__.__dict__.setdefault('__IPYTHON__active',0)

        # Inform the user of ipython's fast exit magics.
        _exit = ' Use @Exit or @Quit to exit without confirmation.'
        __builtin__.exit += _exit
        __builtin__.quit += _exit

        # Create the namespace where the user will operate:

        # FIXME. For some strange reason, __builtins__ is showing up at user
        # level as a dict instead of a module. This is a manual fix, but I
        # should really track down where the problem is coming from. Alex
        # Schmolck reported this problem first.
        if user_ns is None:

            # Set __name__ to __main__ to better match the behavior of the
            # normal interpreter.
            self.user_ns = {'__name__':'__main__',
                            name:self,
                            '__builtins__' : __builtin__,
                            }
        else:
            self.user_ns = user_ns

        # We need to insert into sys.modules something that looks like a
        # module but which accesses the IPython namespace, for shelve and
        # pickle to work interactively. Normally they rely on getting
        # everything out of __main__, but for embedding purposes each IPython
        # instance has its own private namespace, so we can't go shoving
        # everything into __main__.

        try:
            main_name = self.user_ns['__name__']
        except KeyError:
            raise KeyError,'user_ns dictionary MUST have a "__name__" key'
        else:
            #print "pickle hack in place"  # dbg
            sys.modules[main_name] = FakeModule(self.user_ns)

        # List of input with multi-line handling.
        # Fill its zero entry, user counter starts at 1
        self.input_hist = InputList(['\n'])

        # list of visited directories
        self.dir_hist = [os.getcwd()]

        # dict of output history
        self.output_hist = {}

        # dict of names to be treated as system aliases.  Each entry in the
        # alias table must be a 2-tuple of the form (N,name), where N is the
        # number of positional arguments of the alias.
        self.alias_table = {}

        # dict of things NOT to alias (keywords and builtins)
        self.no_alias = {}
        for key in keyword.kwlist:
            self.no_alias[key] = 1
        self.no_alias.update(__builtin__.__dict__)
        
        # make global variables for user access to these
        self.user_ns['_ih'] = self.input_hist
        self.user_ns['_oh'] = self.output_hist
        self.user_ns['_dh'] = self.dir_hist

        # user aliases to input and output histories
        self.user_ns['In']  = self.input_hist
        self.user_ns['Out'] = self.output_hist

        # class initializations
        code.InteractiveConsole.__init__(self,locals = self.user_ns)
        Logger.__init__(self,log_ns = self.user_ns)
        Magic.__init__(self)
        # an ugly hack to get a pointer to the shell, so I can start writing magic
        # code via this pointer instead of the current mixin salad.
        Magic.set_shell(self,self)

        # hooks is a Struct holding pointers to various system hooks, and will
        # be used for further user-side customizations in the future
        #self.hooks = Struct(ps1 = sys.ps1,ps2 = sys.ps2,display = sys.displayhook)
        self.hooks = Struct()

        self.name = name

        self.usage_min =  """\
        An enhanced console for Python.
        Some of its features are:
        - Readline support if the readline library is present.
        - Tab completion in the local namespace.
        - Logging of input, see command-line options.
        - System shell escape via ! , eg !ls.
        - Magic commands, starting with a @ (like @ls, @pwd, @cd, etc.)
        - Keeps track of locally defined variables via @who, @whos.
        - Show object information with a ? eg ?x or x? (use ?? for more info).
        """
        if usage: self.usage = usage
        else: self.usage = self.usage_min

        # Storage
        self.rc = rc   # This will hold all configuration information
        self.inputcache = []
        self._boundcache = []
        self.pager = 'less'
        # temporary files used for various purposes.  Deleted at exit.
        self.tempfiles = []

        # for pushd/popd management
        try:
            self.home_dir = get_home_dir()
        except HomeDirError:
            if os.name == 'dos':  # final, desperate hack for Win9x
                self.home_dir = os.path.join('C:','Program Files','IPython')
            else:
                print 'Unsupported operating system:',os.name
                print 'Exiting...'
                sys.exit()
        self.dir_stack = [os.getcwd().replace(self.home_dir,'~')]

        # Function to call the underlying shell.  Similar to os.system, but it
        # doesn't return a value, and it allows interpolation of variables in
        # the user's namespace.
        self.system = lambda cmd: shell(str(ItplNS(cmd.replace('#','\#'),
                                                   self.user_ns)),
                                        header='IPython system call: ',
                                        verbose=self.rc.system_verbose)
        # Similar one for getoutputerror.
        self.getoutputerror = lambda cmd: \
                              getoutputerror(str(ItplNS(cmd.replace('#','\#'),
                                                        self.user_ns)),
                                             header='IPython system call: ',
                                             verbose=self.rc.system_verbose)
    
        # escapes for automatic behavior on the command line
        self.ESC_SHELL = '!'
        self.ESC_HELP  = '?'
        self.ESC_MAGIC = '@'
        self.ESC_QUOTE = ','
        self.ESC_PAREN = '/'

        # And their associated handlers
        self.esc_handlers = {self.ESC_PAREN:self.handle_auto,
                             self.ESC_QUOTE:self.handle_auto,
                             self.ESC_MAGIC:self.handle_magic,
                             self.ESC_HELP:self.handle_help,
                             self.ESC_SHELL:self.handle_shell_escape,
			     }

        # RegExp for splitting line contents into pre-char//first word-method//rest
        # update the regexp if the above escapes are changed

        # Don't get carried away with trying to make the autocalling catch too
        # much:  it's better to be conservative rather than to trigger hidden
        # evals() somewhere and end up causing side effects.

        self.line_split = re.compile(r'(^[\s*!\?@,/]?)([\?\w\.]+\w*\s*)(\(?.*$)')

        # RegExp to identify potential function names
        self.re_fun_name = re.compile (r'[a-zA-Z_]([a-zA-Z0-9_.]*) *$')
        # RegExp to identify potential function names
        self.re_exclude_auto = re.compile ('^[!=()<>,\*/\+-]|^is ')
        # try to catch also methods for stuff in lists/tuples/dicts: off
        # (experimental). For this to work, the line_split regexp would need
        # to be modified so it wouldn't break things at '['. That line is
        # nasty enough that I shouldn't change it until I can test it _well_.
        #self.re_fun_name = re.compile (r'[a-zA-Z_]([a-zA-Z0-9_.\[\]]*) ?$')

        # keep track of where we started running (mainly for crash post-mortem)
        self.starting_dir = os.getcwd()

        # Attributes for Logger mixin class, make defaults here
        self._dolog = 0
        self.LOG = ''
        self.LOGDEF = '.InteractiveShell.log'
        self.LOGMODE = 'over'
        self.LOGHEAD = Itpl(
"""#log# Automatic Logger file. *** THIS MUST BE THE FIRST LINE ***
#log# DO NOT CHANGE THIS LINE OR THE TWO BELOW
#log# opts = $self.rc.opts
#log# args = $self.rc.args
#log# It is safe to make manual edits below here.
#log#-----------------------------------------------------------------------
""")
        # Various switches which can be set
        self.CACHELENGTH = 5000  # this is cheap, it's just text
        self.BANNER = itpl("Python $sys.version on $sys.platform\n"
        "$sys.copyright\nIPP\nType ? for more help\n")
        # TraceBack handlers:
        # Need two, one for syntax errors and one for other exceptions.
        # plain/color
        self.SyntaxTB = ultraTB.ListTB(color_scheme='NoColor')
        # This one is initialized with an offset, meaning we always want to
        # remove the topmost item in the traceback, which is our own internal
        # code. Valid modes: plain/color/verbose
        self.InteractiveTB = ultraTB.AutoFormattedTB(mode = 'Plain',
                                                     color_scheme='NoColor',
                                                     tb_offset = 1)

        # Object inspector
        ins_colors = OInspect.InspectColors
        code_colors = PyColorize.ANSICodeColors
        self.inspector = OInspect.Inspector(ins_colors,code_colors,'NoColor')
        self.autoindent = 0
        # Make some aliases automatically
        # Prepare list of shell aliases to auto-define
        if os.name == 'posix':            
            auto_alias = ('mkdir mkdir', 'rmdir rmdir',
                          'mv mv -i','rm rm -i','rmf rm -f','cp cp -i',
                          'cat cat','less less','clear clear',
                          # a better ls
                          'ls ls -F',
                          # long ls
                          'll ls -lF',
                          # color ls
                          'lc ls -F -o --color',
                          # ls normal files only
                          'lf ls -F -o --color %l | grep ^-',
                          # ls symbolic links 
                          'lk ls -F -o --color %l | grep ^l',
                          # directories or links to directories,
                          'ldir ls -F -o --color %l | grep /$',
                          # things which are executable
                          'lx ls -F -o --color %l | grep ^-..x',
                          )
        elif os.name in ['nt','dos']:
            auto_alias = ('dir dir /on', 'ls dir /on',
                          'ddir dir /ad /on', 'ldir dir /ad /on',
                          'mkdir mkdir','rmdir rmdir','echo echo',
                          'ren ren','cls cls','cp copy','copy copy',
                          'more type','type type')
        else:
            auto_alias = ()
        self.auto_alias = map(lambda s:s.split(None,1),auto_alias)
        # Call the actual (public) initializer
        self.init_auto_alias()
    # end __init__

    def post_config_initialization(self):
        """Post configuration init method

        This is called after the configuration files have been processed to
        'finalize' the initialization."""
        
        # dynamic data that survives through sessions
        # XXX make the filename a config option?
        persist_base = 'persist'
        if self.rc.profile:
            persist_base += '_%s' % self.rc.profile
        self.persist_fname =  os.path.join(self.rc.ipythondir,persist_base)

        try:
            self.persist = pickle.load(file(self.persist_fname))
        except:
            self.persist = {}
            
    def init_auto_alias(self):
        """Define some aliases automatically.

        These are ALL parameter-less aliases"""
        for alias,cmd in self.auto_alias:
            self.alias_table[alias] = (0,cmd)

    def alias_table_validate(self,verbose=0):
        """Update information about the alias table.

        In particular, make sure no Python keywords/builtins are in it."""

        no_alias = self.no_alias
        for k in self.alias_table.keys():
            if k in no_alias:
                del self.alias_table[k]
                if verbose:
                    print ("Deleting alias <%s>, it's a Python "
                           "keyword or builtin." % k)

    def set_autoindent(self,value=None):
        """Set the autoindent flag, checking for readline support.

        If called with no arguments, it acts as a toggle."""

        if not self.has_readline:
            if os.name == 'posix':
                warn("The auto-indent feature requires the readline library")
            self.autoindent = 0
            return
        if value is None:
            self.autoindent = not self.autoindent
        else:
            self.autoindent = value

    def rc_set_toggle(self,rc_field,value=None):
        """Set or toggle a field in IPython's rc config. structure.

        If called with no arguments, it acts as a toggle.

        If called with a non-existent field, the resulting AttributeError
        exception will propagate out."""

        rc_val = getattr(self.rc,rc_field)
        if value is None:
            value = not rc_val
        setattr(self.rc,rc_field,value)

    def user_setup(self,ipythondir,rc_suffix,mode='install'):
        """Install the user configuration directory.

        Can be called when running for the first time or to upgrade the user's
        .ipython/ directory with the mode parameter. Valid modes are 'install'
        and 'upgrade'."""

        def wait():
            raw_input("Please press <RETURN> to start IPython.")
            print '*'*70

        cwd = os.getcwd()  # remember where we started
        glb = glob.glob
        print '*'*70
        if mode == 'install':
            print \
"""Welcome to IPython. I will try to create a personal configuration directory
where you can customize many aspects of IPython's functionality in:\n"""
        else:
            print 'I am going to upgrade your configuration in:'

        print ipythondir

        rcdirend = os.path.join('IPython','UserConfig')
        cfg = lambda d: os.path.join(d,rcdirend)
        try:
            rcdir = filter(os.path.isdir,map(cfg,sys.path))[0]
        except IOError:
            warning = """
Installation error. IPython's directory was not found.

Check the following:

The ipython/IPython directory should be in a directory belonging to your
PYTHONPATH environment variable (that is, it should be in a directory
belonging to sys.path). You can copy it explicitly there or just link to it.

IPython will proceed with builtin defaults.
"""
            warn(warning)
            wait()
            return

        if mode == 'install':
            try:
                shutil.copytree(rcdir,ipythondir)
                os.chdir(ipythondir)
                rc_files = glb("ipythonrc*")
                for rc_file in rc_files:
                    os.rename(rc_file,rc_file+rc_suffix)
            except:
                warning = """

There was a problem with the installation:
%s
Try to correct it or contact the developers if you think it's a bug.
IPython will proceed with builtin defaults.""" % sys.exc_info()[1]
                warn(warning)
                wait()
                return

        elif mode == 'upgrade':
            try:
                os.chdir(ipythondir)
            except:
                print """
Can not upgrade: changing to directory %s failed. Details:
%s
""" % (ipythondir,sys.exc_info()[1])
                wait()
                return
            else:
                sources = glb(os.path.join(rcdir,'[A-Za-z]*'))
                for new_full_path in sources:
                    new_filename = os.path.basename(new_full_path)
                    if new_filename.startswith('ipythonrc'):
                        new_filename = new_filename + rc_suffix
                    if os.path.exists(new_filename):
                        os.rename(new_filename,new_filename+'.old')
                    shutil.copy(new_full_path,new_filename)
        else:
            raise ValueError,'unrecognized mode for install:',`mode`

        # Fix line-endings to those native to each platform in the config
        # directory.
        try:
            os.chdir(ipythondir)
        except:
            print """
Problem: changing to directory %s failed.
Details:
%s

Some configuration files may have incorrect line endings.  This should not
cause any problems during execution.  """ % (ipythondir,sys.exc_info()[1])
            wait()
        else:
            for fname in glb('ipythonrc*'):
                try:
                    native_line_ends(fname,backup=0)
                except IOError:
                    pass

        if mode == 'install':
            print """
Successful installation!

Please read the sections 'Initial Configuration' and 'Quick Tips' in the
IPython manual (there are both HTML and PDF versions supplied with the
distribution) to make sure that your system environment is properly configured
to take advantage of IPython's features."""
        else:
            print """
Successful upgrade!

All files in your directory:
%(ipythondir)s
which would have been overwritten by the upgrade were backed up with a .old
extension.  If you had made particular customizations in those files you may
want to merge them back into the new files.""" % locals()
        wait()
        os.chdir(cwd)
        # end user_setup()

    def atexit_operations(self):
        """This will be executed at the time of exit.

        Saving of persistent data should be performed here. """

        # input history
        self.savehist()

        # Cleanup all tempfiles left around
        for tfile in self.tempfiles:
            try:
                os.unlink(tfile)
            except OSError:
                pass

        # save the "persistent data" catch-all dictionary
        pickle.dump(self.persist, open(self.persist_fname,"w"))
        
    def savehist(self):
        """Save input history to a file (via readline library)."""
        try:
            self.readline.write_history_file(self.histfile)
        except:
            print 'Unable to save IPython command history to file: ' + \
                  `self.histfile`

    def pre_readline(self):
        """readline hook to be used at the start of each line.

        Currently it handles auto-indent only."""
        
        self.readline.insert_text(' '* self.readline_indent)

    def init_readline(self):
        """Command history completion/saving/reloading."""
        try:
            import readline
            self.Completer = MagicCompleter(self.user_ns,
                                            self.rc.readline_omit__names,
                                            self.alias_table)
        except ImportError,NameError:
            # If FlexCompleter failed to import, MagicCompleter won't be 
            # defined.  This can happen because of a problem with readline
            self.has_readline = 0
            # no point in bugging windows users with this every time:
            if os.name == 'posix':
                warn('Readline services not available on this platform.')
        else:
            import atexit

            # Load user's initrc file (readline config)
            inputrc_name = os.environ.get('INPUTRC')
            if inputrc_name is None:
                home_dir = get_home_dir()
                if home_dir is not None:
                    inputrc_name = os.path.join(home_dir,'.inputrc')
            if os.path.isfile(inputrc_name):
                try:
                    readline.read_init_file(inputrc_name)
                except:
                    warn('Problems reading readline initialization file <%s>'
                         % inputrc_name)
            
            self.has_readline = 1
            self.readline = readline
            self.readline_indent = 0  # for auto-indenting via readline
            # save this in sys so embedded copies can restore it properly
            sys.ipcompleter = self.Completer.complete
            readline.set_completer(self.Completer.complete)

            # Configure readline according to user's prefs
            for rlcommand in self.rc.readline_parse_and_bind:
                readline.parse_and_bind(rlcommand)

            # remove some chars from the delimiters list
            delims = readline.get_completer_delims()
            delims = delims.translate(string._idmap,
                                      self.rc.readline_remove_delims)
            readline.set_completer_delims(delims)
            # otherwise we end up with a monster history after a while:
            readline.set_history_length(1000)
            try:
                #print '*** Reading readline history'  # dbg
                readline.read_history_file(self.histfile)
            except IOError:
                pass  # It doesn't exist yet.

            atexit.register(self.atexit_operations)
            del atexit

        # Configure auto-indent for all platforms
        self.set_autoindent(self.rc.autoindent)

    def showsyntaxerror(self, filename=None):
        """Display the syntax error that just occurred.

        This doesn't display a stack trace because there isn't one.

        If a filename is given, it is stuffed in the exception instead
        of what was there before (because Python's parser always uses
        "<string>" when reading from a string).
        """
        type, value, sys.last_traceback = sys.exc_info()
        sys.last_type = type
        sys.last_value = value
        if filename and type is SyntaxError:
            # Work hard to stuff the correct filename in the exception
            try:
                msg, (dummy_filename, lineno, offset, line) = value
            except:
                # Not the format we expect; leave it alone
                pass
            else:
                # Stuff in the right filename
                try:
                    # Assume SyntaxError is a class exception
                    value = SyntaxError(msg, (filename, lineno, offset, line))
                except:
                    # If that failed, assume SyntaxError is a string
                    value = msg, (filename, lineno, offset, line)
        self.SyntaxTB(type,value,[])

    def debugger(self):
        """Call the pdb debugger."""

        if not self.rc.pdb:
            return
        pdb.pm()

    def showtraceback(self,exc_tuple = None):
        """Display the exception that just occurred."""

        # Though this won't be called by syntax errors in the input line,
        # there may be SyntaxError cases whith imported code.
        if exc_tuple is None:
            type, value, tb = sys.exc_info()
        else:
            type, value, tb = exc_tuple
        if type is SyntaxError:
            self.showsyntaxerror()
        else:
            sys.last_type = type
            sys.last_value = value
            sys.last_traceback = tb
            self.InteractiveTB()
            if self.InteractiveTB.call_pdb and self.has_readline:
                # pdb mucks up readline, fix it back
                self.readline.set_completer(self.Completer.complete)

    def update_cache(self, line):
        """puts line into cache"""
        self.inputcache.insert(0, line) # This copies the cache every time ... :-(
        if len(self.inputcache) >= self.CACHELENGTH:
            self.inputcache.pop()    # This not :-)

    def name_space_init(self):
        """Create local namespace."""
        # We want this to be a method to facilitate embedded initialization.
        code.InteractiveConsole.__init__(self,self.user_ns)

    def mainloop(self):
        """Creates the local namespace and starts the mainloop"""
        self.name_space_init()
        if self.rc.c:  # Emulate Python's -c option
            self.exec_init_cmd()
        self.interact(self.BANNER)

    def exec_init_cmd(self):
        """Execute a command given at the command line.

        This emulates Python's -c option."""

        sys.argv = ['-c']
        self.push(self.rc.c)

    def embed_mainloop(self,header='',local_ns=None,global_ns=None,stack_depth=0):
        """Embeds IPython into a running python program.

        Input:

          - header: An optional header message can be specified.

          - local_ns, global_ns: working namespaces. If given as None, the
          IPython-initialized one is updated with __main__.__dict__, so that
          program variables become visible but user-specific configuration
          remains possible.

          - stack_depth: specifies how many levels in the stack to go to
          looking for namespaces (when local_ns and global_ns are None).  This
          allows an intermediate caller to make sure that this function gets
          the namespace from the intended level in the stack.  By default (0)
          it will get its locals and globals from the immediate caller.

        Warning: it's possible to use this in a program which is being run by
        IPython itself (via @run), but some funny things will happen (a few
        globals get overwritten). In the future this will be cleaned up, as
        there is no fundamental reason why it can't work perfectly."""

        # Patch for global embedding to make sure that things don't overwrite
        # user globals accidentally. Thanks to Richard <rxe@renre-europe.com>
        # FIXME. Test this a bit more carefully (the if.. is new)
        if local_ns is None and global_ns is None:
            self.user_ns.update(__main__.__dict__)


        # Get locals and globals from caller
        call_frame = sys._getframe(stack_depth).f_back

        if local_ns is None:
            local_ns = call_frame.f_locals
        if global_ns is None:
            global_ns = call_frame.f_globals

        # Update namespaces and fire up interpreter
        self.user_ns.update(local_ns)
        self.interact(header)

        # Remove locals from namespace
        for k in local_ns.keys():
            del self.user_ns[k]

    def interact(self, banner=None):
        """Closely emulate the interactive Python console.

        The optional banner argument specify the banner to print
        before the first interaction; by default it prints a banner
        similar to the one printed by the real Python interpreter,
        followed by the current class name in parentheses (so as not
        to confuse this with the real interpreter -- since it's so
        close!).

        """
        cprt = 'Type "copyright", "credits" or "license" for more information.'
        if banner is None:
            self.write("Python %s on %s\n%s\n(%s)\n" %
                       (sys.version, sys.platform, cprt,
                        self.__class__.__name__))
        else:
            sys.stdout.write(banner)

        more = 0

        # Mark activity in the builtins
        __builtin__.__dict__['__IPYTHON__active'] += 1
        while 1:
            try:
                if more:
                    prompt = self.outputcache.prompt2
                    if self.autoindent:
                        self.readline.set_startup_hook(self.pre_readline)
                else:
                    prompt = self.outputcache.prompt1
                try:
                    line = self.raw_input(prompt)
                    if self.autoindent:
                        self.readline.set_startup_hook(None)
                except EOFError:
                    if self.autoindent:
                        self.readline.set_startup_hook(None)
                    self.write("\n")
                    if self.rc.confirm_exit:
                        if ask_yes_no('Do you really want to exit ([y]/n)?','y'):
                            break
                    else:
                        break
                else:
                    more = self.push(line)
                    # Auto-indent management
                    if self.autoindent:
                        if line:
                            ini_spaces = re.match('^(\s+)',line)
                            if ini_spaces:
                                nspaces = ini_spaces.end()
                            else:
                                nspaces = 0
                            self.readline_indent = nspaces

                            if line[-1] == ':':
                                self.readline_indent += 4
                            elif re.match(r'^\s+raise|^\s+return',line):
                                self.readline_indent -= 4
                        else:
                            self.readline_indent = 0

            except KeyboardInterrupt:
                self.write("\nKeyboardInterrupt\n")
                self.resetbuffer()
                more = 0
                # keep cache in sync with the prompt counter:
                self.outputcache.prompt_count -= 1

                if self.autoindent:
                    self.readline_indent = 0

            except SystemExit:
                # If a SystemExit gets here, it's from an IPython @Exit call
                break

            except bdb.BdbQuit:
                warn("The Python debugger has exited with a BdbQuit exception.\n"
                     "Because of how pdb handles the stack, it is impossible\n"
                     "for IPython to properly format this particular exception.\n"
                     "IPython will resume normal operation.")
            except:
                # We should never get here except in fairly bizarre situations
                # (or b/c of an IPython bug). One reasonable exception is if
                # the user sets stdin/out/err to a broken object (or closes
                # any of them!)
		
                fixed_in_out_err = 0

                # Call the Term I/O class and have it reopen any stream which
                # the user might have closed.
                Term.reopen_all()
		
                # Do the same manually for sys.stderr/out/in
		
                # err first, so we can print at least warnings
                if sys.__stderr__.closed:
                    sys.__stderr__ = os.fdopen(os.dup(2),'w',0)
                    fixed_err_err = 1
                    print >> sys.__stderr__,"""
WARNING:
sys.__stderr__ was closed!
I've tried to reopen it, but bear in mind that things may not work normally
from now.  In particular, readline support may have broken.
"""
                # Next, check stdin/out    
                if sys.__stdin__.closed:
                    sys.__stdin__ = os.fdopen(os.dup(0),'r',0)
                    fixed_in_out_err = 1
                    print >> sys.__stderr__,"""
WARNING:
sys.__stdin__ was closed!
I've tried to reopen it, but bear in mind that things may not work normally
from now.  In particular, readline support may have broken.
"""		    
                if sys.__stdout__.closed:
                    sys.__stdout__ = os.fdopen(os.dup(1),'w',0)
                    fixed_in_out_err = 1
                    print >> sys.__stderr__,"""
WARNING:
sys.__stdout__ was closed!
I've tried to reopen it, but bear in mind that things may not work normally
from now.  In particular, readline support may have broken.
"""		    

                # Now, check mismatch of objects
                if sys.stdin is not sys.__stdin__:
                    sys.stdin = sys.__stdin__
                    fixed_in_out_err = 1
                    print >> sys.__stderr__,"""
WARNING:
sys.stdin has been reset to sys.__stdin__.
There seemed to be a problem with your sys.stdin.
"""
                if sys.stdout is not sys.__stdout__:
                    sys.stdout = sys.__stdout__
                    fixed_in_out_err = 1
                    print >> sys.__stderr__,"""
WARNING:
sys.stdout has been reset to sys.__stdout__.
There seemed to be a problem with your sys.stdout.
"""

                if sys.stderr is not sys.__stderr__:
                    sys.stderr = sys.__stderr__
                    fixed_in_out_err = 1
                    print >> sys.__stderr__,"""
WARNING:
sys.stderr has been reset to sys.__stderr__.
There seemed to be a problem with your sys.stderr.
"""
                # If the problem wasn't a broken out/err, it's an IPython bug
                # I wish we could ask the user whether to crash or not, but
                # calling any function at this point messes up the stack.
                if not fixed_in_out_err:
                    raise
                
        # We are off again...
        __builtin__.__dict__['__IPYTHON__active'] -= 1

    def excepthook(self, type, value, tb):
      """One more defense for GUI apps that call sys.excepthook.

      GUI frameworks like wxPython trap exceptions and call
      sys.excepthook themselves.  I guess this is a feature that
      enables them to keep running after exceptions that would
      otherwise kill their mainloop. This is a bother for IPython
      which excepts to catch all of the program exceptions with a try:
      except: statement.

      Normally, IPython sets sys.excepthook to a CrashHandler instance, so if
      any app directly invokes sys.excepthook, it will look to the user like
      IPython crashed.  In order to work around this, we can disable the
      CrashHandler and replace it with this excepthook instead, which prints a
      regular traceback using our InteractiveTB.  In this fashion, apps which
      call sys.excepthook will generate a regular-looking exception from
      IPython, and the CrashHandler will only be triggered by real IPython
      crashes.

      This hook should be used sparingly, only in places which are not likely
      to be true IPython errors.
      """
      
      self.InteractiveTB(type, value, tb, tb_offset=0)
      if self.InteractiveTB.call_pdb and self.has_readline:
          self.readline.set_completer(self.Completer.complete)

    def call_alias(self,alias,rest=''):
        """Call an alias given its name and the rest of the line.

        This function MUST be given a proper alias, because it doesn't make
        any checks when looking up into the alias table.  The caller is
        responsible for invoking it only with a valid alias."""

        #print 'ALIAS: <%s>+<%s>' % (alias,rest) # dbg
        nargs,cmd = self.alias_table[alias]
        # Expand the %l special to be the user's input line
        if cmd.find('%l') >= 0:
            cmd = cmd.replace('%l',rest)
            rest = ''
        if nargs==0:
            # Simple, argument-less aliases
            cmd = '%s %s' % (cmd,rest)
        else:
            # Handle aliases with positional arguments
            args = rest.split(None,nargs)
            if len(args)< nargs:
                error('Alias <%s> requires %s arguments, %s given.' %
                      (alias,nargs,len(args)))
                return
            cmd = '%s %s' % (cmd % tuple(args[:nargs]),' '.join(args[nargs:]))
        # Now call the macro, evaluating in the user's namespace
        try:
            # flush stdout so we don't mangle python's buffering
            sys.stdout.flush()
            self.system(cmd)
        except:
            self.showtraceback()

    def runcode(self,code_obj):
        """Execute a code object.

        When an exception occurs, self.showtraceback() is called to display a
        traceback."""

        # Set our own excepthook in case the user code tries to call it
        # directly, so that the IPython crash handler doesn't get triggered
        old_excepthook,sys.excepthook = sys.excepthook, self.excepthook
        try:
            try:
                exec code_obj in self.locals
            finally:
                # Reset our crash handler in place
                sys.excepthook = old_excepthook

        except SystemExit,msg:
            if str(msg)=='IPythonExit':
                raise
            else:
                self.resetbuffer()
                self.showtraceback()
                warn( __builtin__.exit,level=1)
        except:
            self.showtraceback()
        else:
            if code.softspace(sys.stdout, 0):
                print

    def raw_input(self, prompt=""):
        """Write a prompt and read a line.

        The returned line does not include the trailing newline.
        When the user enters the EOF key sequence, EOFError is raised.

        The base implementation uses the built-in function
        raw_input(); a subclass may replace this with a different
        implementation.
        """
        return self.prefilter(raw_input(prompt),
                              prompt==self.outputcache.prompt2)
        
    def split_user_input(self,line):
        """Split user input into pre-char, function part and rest."""

        lsplit = self.line_split.match(line)
        if lsplit is None:  # no regexp match returns None
            line = line.rstrip()
            ini_spaces = re.match('^(\s+)',line)
            if ini_spaces:
                nspaces = ini_spaces.end()
            else:
                nspaces = 0

            pre = ' '*nspaces
            try:
                iFun,theRest = line.split(None,1)
            except ValueError:
                iFun,theRest = line,''
        else:
            pre,iFun,theRest = lsplit.groups()
        #print 'pre <%s> iFun <%s> rest <%s>' % (pre,iFun.strip(),theRest)  # dbg
        return pre,iFun.strip(),theRest

    def _prefilter(self, line, continue_prompt):
        """Calls different preprocessors, depending on the form of line."""

        # All handlers *must* return a value, even if it's blank ('').

        # Lines are NOT logged here. Handlers should process the line as
        # needed, update the cache AND log it (so that the input cache array
        # stays synced).

        # This function is _very_ delicate, and since it's also the one which
        # determines IPython's response to user input, it must be as efficient
        # as possible.  For this reason it has _many_ returns in it, trying
        # always to exit as quickly as it can figure out what it needs to do.

        # This function is the main responsible for maintaining IPython's
        # behavior respectful of Python's semantics.  So be _very_ careful if
        # making changes to anything here.

        #.....................................................................
        # Code begins

        #if line.startswith('@crash'): raise RuntimeError,'Crash now!'  # dbg

        # save the line away in case we crash, so the post-mortem handler can
        # record it
        self._last_input_line = line

        #print '***line: <%s>' % line # dbg

        # the input history needs to track even empty lines
        if not line.strip():
            if not continue_prompt:
                self.outputcache.prompt_count -= 1
            return self.handle_normal('',continue_prompt)

        # print '***cont',continue_prompt  # dbg
        # special handlers are only allowed for single line statements
        if continue_prompt and not self.rc.multi_line_specials:
            return self.handle_normal(line,continue_prompt)

        # First check for explicit escapes in the last/first character
        handler = None
        if line[-1] == self.ESC_HELP:
            handler = self.esc_handlers.get(line[-1])  # the ? can be at the end
        if handler is None:
            handler = self.esc_handlers.get(line[0])
        if handler is not None:
            return handler(line,continue_prompt)

        # Emacs ipython-mode tags certain input lines
        if line.endswith('# PYTHON-MODE'):
            return self.handle_emacs(line,continue_prompt)

        # Next, check if we can automatically execute this thing
        pre,iFun,theRest = self.split_user_input(line)
        #print 'pre <%s> iFun <%s> rest <%s>' % (pre,iFun,theRest)  # dbg

        # Allow ! in multi-line statements if multi_line_specials is on:
        if continue_prompt and self.rc.multi_line_specials and \
               not pre.strip() and iFun.startswith(self.ESC_SHELL):
            return self.handle_shell_escape(line,continue_prompt,
                                            pre=pre,iFun=iFun,theRest=theRest)

        # Let's try to find if the input line is a magic fn
        oinfo = None
        if hasattr(self,'magic_'+iFun):
            oinfo = self._ofind(iFun) # FIXME - _ofind is part of Magic
            if oinfo['ismagic']:
                # Be careful not to call magics when a variable assignment is
                # being made (ls='hi', for example)
                if self.rc.automagic and \
                       (len(theRest)==0 or theRest[0] not in '!=()<>,') and \
                       not continue_prompt:
                    return self.handle_magic('@'+line.lstrip(),continue_prompt)
                else:
                    return self.handle_normal(line,continue_prompt)

        if oinfo is None:
            oinfo = self._ofind(iFun) # FIXME - _ofind is part of Magic

        if not oinfo['found']:
            return self.handle_normal(line,continue_prompt)
        else:
            #print 'iFun <%s> rest <%s>' % (iFun,theRest) # dbg
            if oinfo['isalias']:
                # Same logic for aliases we had for magics: give precedence
                # to normal python code so an alias can be redefined as a
                # variable, for example.
                if len(theRest)==0 or theRest[0] not in '!=()<>,':
                    return self.handle_alias(line,continue_prompt,
                                             pre,iFun,theRest)
                else:
                    return self.handle_normal(line,continue_prompt)

            if self.rc.autocall and \
                   not self.re_exclude_auto.match(theRest) and \
                   self.re_fun_name.match(iFun) and \
                   callable(oinfo['obj']) :
                #print 'going auto'  # dbg
                return self.handle_auto(line,continue_prompt)
            else:
                #print 'was callable?', callable(oinfo['obj'])  # dbg
                return self.handle_normal(line,continue_prompt)

        # If we get here, we have a normal Python line. Log and return.
        return self.handle_normal(line,continue_prompt)

    def _prefilter_dumb(self, line, continue_prompt):
        """simple prefilter function, for debugging"""
        return self.handle_normal(line,continue_prompt)

    # Set the default prefilter() function (this can be user-overridden)
    prefilter = _prefilter

    def handle_normal(self,line,continue_prompt):
        """Handle normal input lines. Use as a template for handlers."""

        self.log(line,continue_prompt)
        self.update_cache(line)
        return line

    def handle_alias(self,line,continue_prompt,pre,iFun,theRest):
        """Handle alias input lines. """

        theRest = theRest.replace("'","\\'")
        line_out = "%s%s.call_alias('%s','%s')" % (pre,self.name,iFun,theRest)
        self.log(line_out,continue_prompt)
        self.update_cache(line_out)
        return line_out

    def handle_shell_escape(self, line, continue_prompt=None,
                            pre=None,iFun=None,theRest=None):
        """Execute the line in a shell, empty return value"""

        # Example of a special handler. Others follow a similar pattern.
        if continue_prompt:  # multi-line statements
            if iFun.startswith('!!'):
                print 'SyntaxError: !! is not allowed in multiline statements'
                return ''
            else:
                cmd = "%s %s" % (iFun[1:],theRest)
                cmd = cmd.replace('"','\\"')
                line_out = '%s%s.system("%s")' % (pre,self.name,cmd)
                                                     
        else: # single-line input
            if line.startswith('!!'):
                return self.handle_magic('@sx %s' % line[2:],continue_prompt)
            else:
                cmd = line[1:].replace('"','\\"')
                line_out = '%s.system("%s")' % (self.name,cmd)
        # update cache/log and return
        self.log(line_out,continue_prompt)
        self.update_cache(line_out)   # readline cache gets normal line
        return line_out

    def handle_magic(self, line, continue_prompt=None):
        """Execute magic functions.

        Also log them with a prepended # so the log is clean Python."""

        #print 'in handle_magic'  # dbg
        self.log('#'+line,continue_prompt)
        self.update_cache(line)
        shell = self.name+'.'
        # remove @ and de-mangle magic name
        line = 'magic_'+ line.strip()[1:]
        try:
            scommand, parameter_s = line.split(' ',1)
        except ValueError: # there is only the command
            parameter_s = ''
            scommand = line
        if hasattr(self, scommand):
            parameter_s = ' %s ' % parameter_s # Protect quotes at the end
            return '%s%s(parameter_s=r"""%s"""[1:-1])' % (shell,scommand,
                                                          parameter_s)
        else:
            return '%s%s()' % (shell,line)

    def handle_auto(self, line, continue_prompt):
        """Hande lines which can be auto-executed, quoting if requested.

        Also log them with a prepended # so the log is clean Python."""

        pre,iFun,theRest = self.split_user_input(line)
        #print '*** Auto: pre <%s> iFun <%s> rest <%s>' % (pre,iFun,theRest) # dbg

        if pre == self.ESC_QUOTE:
            # Auto-quote
            newcmd = iFun + '("' + '", "'.join(theRest.split()) + '")\n'
        else:
            # Auto-paren
            if theRest.startswith('='):
                return iFun + ' '+theRest+'\n'
            newcmd = iFun.rstrip() + '(' + theRest + ')\n'

        print >>Term.cout, self.outputcache.prompt1.auto_rewrite() + newcmd,
        # log what is now valid Python, not the actual user input (without end \n)
        self.log(newcmd.strip(),continue_prompt)
        return newcmd

    def handle_help(self, line, continue_prompt):
        """Try to get some help for the object.

        obj? or ?obj   -> basic information.
        obj?? or ??obj -> more details.
        """

        # We need to make sure that we don't process lines which would be
        # otherwise valid python, such as "x=1 # what?"
        try:
            code.compile_command(line)
        except SyntaxError:
            # We should only handle as help stuff which is NOT valid syntax
            if line[0]==self.ESC_HELP:
                line = line[1:]
            elif line[-1]==self.ESC_HELP:
                line = line[:-1]
            self.log('#?'+line)
            self.update_cache(line)
            if line:
                self.magic_pinfo(line)
            else:
                page(self.usage,screen_lines=self.rc.screen_length)
            return '' # Empty string is needed here!
        except:
            # Pass any other exceptions through to the normal handler
            return self.handle_normal(line,continue_prompt)
        else:
            # If the code compiles ok, we should handle it normally
            return self.handle_normal(line,continue_prompt)

    def handle_emacs(self,line,continue_prompt):
        """Handle input lines marked by python-mode."""

        # Currently, nothing is done.  Later more functionality can be added
        # here if needed.

        # The input cache shouldn't be updated

        return line

    def safe_execfile(self,fname,*where,**kw):
        fname = os.path.expanduser(fname)

        # find things also in current directory
        dname = os.path.dirname(fname)
        if not sys.path.count(dname):
            sys.path.append(dname)

        try:
            xfile = open(fname)
        except:
            print >> sys.stderr, \
                  'Could not open file <%s> for safe execution.' % fname
            return None

        kw.setdefault('islog',0)
        kw.setdefault('quiet',1)
        first = xfile.readline()
        _LOGHEAD = str(self.LOGHEAD).split('\n',1)[0].strip()
        xfile.close()
        xfile = open(fname)
        # line by line execution
        if first.startswith(_LOGHEAD) or kw['islog']:
            print 'Loading log file <%s> one line at a time...' % fname
            if kw['quiet']:
                stdout_save = sys.stdout
                sys.stdout = StringIO.StringIO()
            try:
                globs,locs = where[0:2]
            except:
                try:
                    globs = locs = where[0]
                except:
                    globs = locs = globals()
            badblocks = []

            # we also need to identify indented blocks of code when replaying
            # logs and put them together before passing them to an exec
            # statement. This takes a bit of regexp and look-ahead work in the
            # file. It's easiest if we swallow the whole thing in memory
            # first, and manually walk through the lines list moving the
            # counter ourselves.
            indent_re = re.compile('\s+\S')
            filelines = xfile.readlines()
            xfile.close()
            nlines = len(filelines)
            lnum = 0
            while lnum < nlines:
                line = filelines[lnum]
                lnum += 1
                # don't re-insert logger status info into cache
                if line.startswith('#log#'):
                    continue
                elif line.startswith('#@'):
                    self.update_cache(line[1:])
                    line = magic2python(line)
                elif line.startswith('#!'):
                    self.update_cache(line[1:])
                else:
                    # build a block of code (maybe a single line) for execution
                    block = line
                    try:
                        next = filelines[lnum] # lnum has already incremented
                    except:
                        next = None
                    while next and indent_re.match(next):
                        block += next
                        lnum += 1
                        try:
                            next = filelines[lnum]
                        except:
                            next = None
                    # now execute the block of one or more lines
                    try:
                        exec block in globs,locs
                        self.update_cache(block.rstrip())
                    except SystemExit:
                        pass
                    except:
                        badblocks.append(block.rstrip())
            if kw['quiet']:  # restore stdout
                sys.stdout.close()
                sys.stdout = stdout_save
            print 'Finished replaying log file <%s>' % fname
            if badblocks:
                print >> sys.stderr, \
                      '\nThe following lines/blocks in file <%s> reported errors:' \
                      % fname
                for badline in badblocks:
                    print >> sys.stderr, badline
        else:  # regular file execution
            try:
                execfile(fname,*where)
            except SyntaxError:
                type, value = sys.exc_info()[0:2]
                self.SyntaxTB(type,value,[])
                warn('Failure executing file: <%s>' % fname)
            except:
                self.InteractiveTB()
                warn('Failure executing file: <%s>' % fname)

#************************* end of file <iplib.py> *****************************
