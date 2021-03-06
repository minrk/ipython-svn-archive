"""
IPython -- An enhanced Interactive Python

Requires Python 2.1 or newer.

This file contains all the classes and helper functions specific to IPython.
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
import os, sys, __main__,__builtin__
import UserList # don't subclass list so this works with Python2.1
import exceptions
import code, glob, types, re, inspect,pydoc,StringIO,shutil,pdb,string
from pprint import pprint,pformat

# Homebrewed modules
from Logger import Logger
from Magic import Magic,magic2python
import OInspect,PyColorize
import ultraTB
from ultraTB import ColorScheme,ColorSchemeTable  # too long names
from usage import cmd_line_usage,interactive_usage
from Struct import Struct
from genutils import *
from Itpl import Itpl,itpl,printpl


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

        def __init__(self, namespace = None, omit__names = 0):
            """MagicCompleter(namespace = None, omit__names = 0) -> completer

            Return a completer object suitable for use by the readline library
            via readline.set_completer().
            
            The optional omit__names parameter sets the completer to omit the
            'magic' names (__magicname__) for python objects unless the text
            to be completed explicitly starts with one or more underscores."""
            
            FlexCompleter.Completer.__init__(self,namespace)
            delims = FlexCompleter.readline.get_completer_delims()
            delims = delims.replace('@','')
            FlexCompleter.readline.set_completer_delims(delims)
            self.omit__names = omit__names

        # Code contributed by Alex Schmolck, for ipython/emacs integration
        def all_completions(self, text):
            """Return all possible completions for the benefit of
            emacs."""
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
            
        def complete(self, text, state):
            """Return the next possible completion for 'text'.

            This is called successively with state == 0, 1, 2, ... until it
            returns None.  The completion should begin with 'text'.  """

            if text.startswith('@'):
                text = text.replace('@','__IP.magic_')
            if text.startswith('~'):
                text = os.path.expanduser(text)
            if state == 0:
                if "." in text:
                    self.matches = self.attr_matches(text)
                    if text.endswith('.') and self.omit__names:
                        # true if txt is _not_ a __ name, false otherwise:
                        no__name = (lambda txt:
                                    re.match(r'.*\.__.*?__',txt) is None)
                        self.matches = filter(no__name,self.matches) 
                else:
                    self.matches = self.global_matches(text)
                    # this is so completion finds magics when automagic is on:
                    if self.matches == [] and not text.startswith(os.sep):
                        self.matches = self.attr_matches('__IP.magic_'+text)
            try:
                return self.matches[state].replace('__IP.magic_','@')
            except IndexError:
                return None

except ImportError:
    print 'IE'
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


class _FakeModule:
    """Simple class with attribute access to fake a module.

    This is not meant to replace a module, but to allow inserting a fake
    module in sys.modules so that systems which rely on run-time module
    importing like shelve and pickle work correctly in initeractive IPython
    sections.

    Do NOT use this code for anything other than this IPython private hack."""

    def __init__(self,adict):
        self.__dict__ = adict

    def __getattr__(self,key):
        return self.__dict__[key]


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
        __builtin__.__dict__['__IPYTHON__'] = self

        # Keep in the builtins a flag for when IPython is active.  We set it
        # with setdefault so that multiple nested IPythons don't clobber one
        # another.  Each will increase its value by one upon being activated,
        # which also gives us a way to determine the nesting level.
        __builtin__.__dict__.setdefault('__IPYTHON__active',0)

        # Create the namespace where the user will operate:

        # FIXME. For some strange reason, __builtins__ is showing up at user
        # level as a dict instead of a module. This is a manual fix, but I
        # should really track down where the problem is coming from. Alex
        # Schmolck reported this problem first.
        if user_ns is None:
            self.user_ns = {'__name__':'__IPYTHON__main__',
                            name:self,
                            '__builtins__' : __builtin__,
                            }
        else:
            self.user_ns = user_ns

        # We need to insert into sys.modules something that looks like a
        # module but which accesses the IPython namespace, for shelve and
        # pickle to work interatctively. Normally they rely on getting
        # everything out of __main__, but for embedding purposes each IPython
        # instance has its own private namespace, so we can't go shoving
        # everything into __main__.
        
        try:
            main_name = self.user_ns['__name__']
        except KeyError:
            raise KeyError,'user_ns dictionary MUST have a "__name__" key'
        else:
            sys.modules[main_name] = _FakeModule(self.user_ns)
            
        # List of input with multi-line handling. 
        # Fill its zero entry, user counter starts at 1
        self.input_hist = InputList(['\n'])

        # list of visited directories
        self.dir_hist = [os.getcwd()]

        # dict of output history
        self.output_hist = {}

        # make global variables for user access to these
        self.user_ns['_ih'] = self.input_hist
        self.user_ns['_oh'] = self.output_hist
        self.user_ns['_dh'] = self.dir_hist

        # user aliases to input and output histories
        self.user_ns['In'] = self.user_ns['_ih']
        self.user_ns['Out'] = self.user_ns['_oh']

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
        Features are:
        - Readline support if present
        - Completion in the local namespace, eg. type TAB twice at the prompt.
        - Logging of input, see command-line options.
        - Systemshell escape by the ! , eg !ls
        - Magic commands, starting with a @ (like @ls, @pwd, @cd, etc.)
        - Keeps track of locally defined variables @who, @whos
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
            
        # escapes for automatic behavior on the command line
        self.ESC_SHELL = '!'
        self.ESC_HELP = '?'
        self.ESC_MAGIC = '@'
        self.ESC_QUOTE = ','
        self.ESC_PAREN = '/'

        # RegExp for splitting line contents into pre-char//first word-method//rest
        # update the regexp if the above escapes are changed
        self.line_split = re.compile(r'(^[\s*!\?@,/]?)([\?\w\.]+\w*\s*)(\(?.*$)')
        # RegExp to identify potential function names

        self.fun_name = re.compile (r'[a-zA-Z_]([a-zA-Z0-9_.]*) ?$')

        # try to catch also methods for stuff in lists/tuples/dicts:
        # off (experimental). For this to work, the line_split regexp would
        # need to be modified so it wouldn't break things at '['. That line
        # is nasty enough that I shouldn't change it until I can test it _well_.
        #self.fun_name = re.compile (r'[a-zA-Z_]([a-zA-Z0-9_.\[\]]*) ?$')

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
        # List of shell commands to auto-define
        if os.name == 'posix':
            auto_shell = {'ls': 'ls -F', 'mkdir': 'mkdir', 'rmdir':'rmdir',
                          'mv':'mv','rm':'rm -i','rmf':'rm -f','less':'less',
                          'cat':'cat','clear':'clear','lc':'ls -F -o --color'}
        elif os.name =='nt':
            auto_shell = {'dir':'dir /on', 'ls':'dir /on',
                          'ddir':'dir /ad /on', 'ld':'dir /ad /on',
                          'mkdir': 'mkdir','rmdir':'rmdir',
                          'ren':'ren','cls':'cls',
                          'more':'type','type':'type' }
        else:
            auto_shell = {}
        for name,cmd in auto_shell.items():
            self.magic_alias(name+' '+cmd)
    # end __init__

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
            except:
                print """
There was a problem with the installation:
%s
Try to correct it or contact the developers if you think it's a bug.
IPython will proceed with builtin defaults.""" % sys.exc_info()[1]
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
                sources = glb(os.path.join(rcdir,'[A-Za-z]*.py'))
                for new_full_path in sources:
                    new_filename = os.path.basename(new_full_path)
                    if new_filename.startswith('ipythonrc'):
                        new_filename = new_filename.replace('.py',rc_suffix)
                    if os.path.exists(new_filename):
                        os.rename(new_filename,new_filename+'.old')
                    shutil.copy(new_full_path,new_filename)
        else:
            raise ValueError,'unrecognized mode for install:',`mode`
        
        # Ugly. This is a hack b/c distutils will only copy files named .py and
        # which seem to be part of a package (with a __init__.py)
        os.chdir(ipythondir)
        for fname in glb('__init__*') + glb('*.pyc') + glb('*py~'):
            try:
                os.remove(fname)
            except:
                pass
        for fname in glb('ipythonrc*.py'):
            os.rename(fname,fname.replace('.py',rc_suffix))
        for fname in glb('*'):
            try:
                native_line_ends(fname,backup=0)
            except IOError:
                pass
        # End of ugly distutils hack

        # Colors just don't work in Windows, disable them.
        # FIXME. This would be better done by loading separate files with the
        # os-specific preferences. Later.
        if os.name in ('nt','dos'):
            iprc_name = 'ipythonrc.ini'
            iprc_bak_name = iprc_name + '.bak'
            os.rename(iprc_name,iprc_bak_name)
            iprc_bak = open(iprc_bak_name,'r')
            iprc = open(iprc_name,'w')
            while 1:
                line = iprc_bak.readline()
                if line =='': break
                if line.find('colors Linux') >= 0:
                    line = '#colors Linux\r\n'
                if line.find('colors NoColor') >= 0:
                    line = 'colors NoColor\r\n'
                iprc.write(line)
                
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

    def savehist(self):
        """Save input history to a file (via readline library)."""
        try:
            self.readline.write_history_file(self.histfile)
        except:
            print 'Unable to save IPython command history to file: ' + \
                  `self.histfile`

    def init_readline(self):
        """Command history completion/saving/reloading."""
        try:
            import readline
            #print '*** Loading readline'  # dbg
            import atexit
            self.has_readline = 1
            self.readline = readline
            self.Completer = MagicCompleter(self.user_ns,
                                            self.rc.readline_omit__names)
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

            atexit.register(self.savehist)
            del atexit
            
        except ImportError,msg:
            self.has_readline = 0
            # no point in bugging windows users with this every time:
            if os.name == 'posix':
                warn('Readline services not available on this platform.')

        except KeyError:
            pass  # under windows, no environ['term'] key

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

    def showtraceback(self):
        """Display the exception that just occurred."""

        # Though this won't be called by syntax errors in the input line,
        # there may be SyntaxError cases whith imported code.
        if sys.exc_info()[0] == SyntaxError:
            self.showsyntaxerror()
        else:
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
        self.interact(self.BANNER)
        self.exit_cleanup()

    def exit_cleanup(self):
        """Cleanup actions to execute at exit time."""
        for tfile in self.tempfiles:
            try:
                os.unlink(tfile)
            except OSError:
                pass

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
                else:
                    prompt = self.outputcache.prompt1
                try:
                    line = self.raw_input(prompt)
                except EOFError:
                    self.write("\n")
                    if self.rc.confirm_exit:
                        if ask_yes_no('Do you really want to exit ([y]/n)?','y'):
                            break
                    else:
                        break
                else:
                    more = self.push(line)
                        
            except KeyboardInterrupt:
                self.write("\nKeyboardInterrupt\n")
                self.resetbuffer()
                more = 0
                # keep cache in sync with the prompt counter:
                self.outputcache.prompt_count -= 1

            except SystemExit:
                # If a SystemExit gets here, it's from an IPython @Exit call
                break
            except:
                # We should never get here except in fairly bizarre situations
                # (or b/c of an IPython bug). One reasonable exception is if
                # the user sets stdout/err to a broken object.
                fix_out_err = 0
                try:
                    print 'Testing sys.sdtout...',
                except:
                    sys.stdout = sys.__stdout__
                    fix_out_err = 1
                    warn(
"""sys.sdtout has been reset to sys.__stdout__.
There seemed to be a problem with your normal sys.stdout.""")
                else:
                    print 'OK.'
                try:
                    print >> sys.stderr, 'Testing sys.sdterr...',
                except:
                    sys.stderr = sys.__stderr__
                    fix_out_err = 1
                    warn(
"""sys.sdterr has been reset to sys.__stderr__.
There seemed to be a problem with your normal sys.stderr.""")
                else:
                    print 'OK.'

                self.showtraceback()

                # If the problem wasn't a broken out/err, it may be a bug
                if not fix_out_err:
                    warn("""
The above exception has been trapped by IPython's 'last line of defense'.

It is likely a bug in IPython. Unless you are positive it is not, it's
probably best to close this IPython session.

IPython can now crash and generate a bug report for the developers. If you
choose to continue, there may be unexpected behavior.
""")
                    crash = ask_yes_no(
'Do you want to let IPython crash and generate a bug report (y/n)?')
                    if crash:
                        raise
                    else:
                        print 'IPython will continue operating.'

        # We are off again...
        __builtin__.__dict__['__IPYTHON__active'] -= 1

    def runcode(self, code_obj):
        """Execute a code object.

        When an exception occurs, self.showtraceback() is called to
        display a traceback.
        """
        try:
            exec code_obj in self.locals

        except SystemExit,msg:
            if str(msg)=='IPythonExit':
                raise
            else:
                self.resetbuffer()
                self.showtraceback()
                warn( __builtins__['exit']+
                     "\nUse @Exit or @Quit to exit without confirmation.",
                      level=1)

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

    def _prefilter(self, line, continue_prompt):
        """Calls different preprocessors, depending on the form of line."""

        # All handlers *must* return a value, even if it's blank ('').

        # Only normal lines are logged here. Handlers should process the line
        # as needed, update the cache AND log it (so that the input cache
        # array stays synced).

        #if line.startswith('@crash'): raise 'Crash now!'  # dbg
        
        # save the line away in case we crash, so the post-mortem handler can
        # record it
        self._last_input_line = line

        # the input history needs to track even empty lines
        if not line.strip():
            return self.handle_normal('',continue_prompt)

        # print '***cont',continue_prompt  # dbg
        # special handlers only allowed for single line statements
        if continue_prompt:
            return self.handle_normal(line,continue_prompt)
        # Break the line into component parts for possible auto-execution
        lsplit = self.line_split.match(line)
        if lsplit is None:  # no regexp match returns None
            iFun,theRest = line,''
            #print 'iFun <%s> rest <%s>' % (iFun,theRest)  # dbg
        else:
            pre,iFun,theRest = lsplit.groups()
            #print 'pre <%s> iFun <%s> rest <%s>' % (pre,iFun,theRest)  # dbg

        # First check for explicit escapes in the first character
        line0 = line[0]
        if line0 == self.ESC_SHELL:
            return self.handle_shell_escape(line)
        # Both ?word and  word? go to help
        if line0 == self.ESC_HELP:
            return self.handle_help(line[1:])
        if line[-1] == self.ESC_HELP:
            return self.handle_help(line[:-1])
        if line0 == self.ESC_MAGIC:
            return self.handle_magic(line)
        if line0 in self.ESC_QUOTE+self.ESC_PAREN:
            return self.handle_auto(line0,iFun,theRest,line)

        # Next, check if we can automatically execute this thing
        try:
            #print 'iFun <%s> theRest <%s>' % (iFun,theRest)  # dbg
            if self.fun_name.match(iFun) and \
               (len(theRest)==0 or theRest[0] not in '!=()<>') and \
               callable( eval(iFun, self.user_ns) ):
                #print 'going auto'  # dbg
                return self.handle_auto(self.ESC_PAREN,iFun,theRest,line)
            elif ' ' in iFun:
                #print 'space in input exception'  # dbg
                raise SpaceInInput  # possible magic
            else:
                #print 'going normal'  # dbg
                return self.handle_normal(line,continue_prompt)

        # Last check for automatically executing magics (lowest priority)
        except (SyntaxError,NameError,AttributeError,ValueError,SpaceInInput):
            #print sys.exc_info()[0:2]  # dbg
            if self.rc.automagic and not theRest.startswith('='):
                try:
                    #print 'checking magic |'+iFun+'|'  # dbg
                    #print 'lsm',self.lsmagic()  # dbg
                    self.lsmagic().index(iFun.strip())
                    #print 'found magic |'+iFun+'|'  # dbg
                    #print 'magic', '@'+line.lstrip()  # dbg
                except ValueError:
                    # Raised by index() when it doesn't find things
                    pass
                else:
                    return self.handle_magic('@'+line.lstrip())

        # If we get here, we have a normal Python line. Log and return.
        return self.handle_normal(line,continue_prompt)

    # Set the default prefilter() function (this can be user-overridden)
    prefilter = _prefilter

    def handle_normal(self,line,continue_prompt):
        """Handle normal input lines. Use as a template for handlers."""
        self.log(line,continue_prompt)
        self.update_cache(line)
        return line
        
    def handle_shell_escape(self, line):
        """Execute the line in a shell, empty return value"""

        # Example of a special handler. Others follow a similar pattern.

        # These lines aren't valid python, so log should comment them out. But
        # the readline cache should have them normally, so they can be
        # retrieved with the arrows. The log and input array _ih should only
        # contain valid python, the readline cache contains anything that was
        # input exactly as it was entered at the prompt.
        
        self.log('#'+line)        # comment out into log/_ih
        self.update_cache(line)   # readline cache gets normal line
        line = line.strip()[1:]
        os.system(line)
        return ''               # MUST return something, at least an empty string
            
    def handle_help(self, line):
        """Try to get some help for the object.

        obj? or ?obj   -> basic information.
        obj?? or ??obj -> more details.
        """

        self.log('#?'+line)
        self.update_cache(line)
        if line:
            self.magic_pinfo(line)
        else:
            page(self.usage,screen_lines=self.rc.screen_length)
        return '' # Empty string is needed here!

    def handle_magic(self, line):
        """Execute magic functions.

        Also log them with a prepended # so the log is clean Python."""
        
        #print 'in handle_magic'  # dbg
        self.log('#'+line)        
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
            if parameter_s.startswith('"'):
                parameter_s = ' ' + parameter_s
            if parameter_s.endswith('"'):
                parameter_s += ' '
            return shell+scommand+'(parameter_s="""%s""")' % (parameter_s,)
        else:
            return shell+line+'()'

    def handle_auto(self, line0, iFun,theRest,line):
        """Hande lines which can be auto-executed, quoting if requested.

        Also log them with a prepended # so the log is clean Python."""

        # print 'auto: '+line0+'|'+iFun+'|'+theRest  # dbg
        if line0 == self.ESC_QUOTE:
            # Auto-quote
            newcmd = iFun + '("' + '", "'.join(theRest.split()) + '")\n'
        else:
            # Auto-paren
            if theRest.startswith('='):
                return iFun + ' '+theRest+'\n'
            newcmd = iFun.rstrip() + '(' + theRest + ')\n'
            
        print self.outputcache.prompt1.auto_rewrite() + newcmd,
        # log what is now valid Python, not the actual user input (without end \n)
        self.log(newcmd.strip())
        return newcmd

    def safe_execfile(self,fname,*where,**kw):
        fname = os.path.expanduser(fname)

        # find things also in current directory
        # patch by RA <ralf_ahlbrink@web.de>
        dname = os.path.dirname(fname)
        if not sys.path.count(dname):
            sys.path.append(dname)
        # end patch by RA <ralf_ahlbrink@web.de>
        
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

                
#-----------------------------------------------------------------------------
# Janko's original Changelog from the IPP days follows. For current
# information, see the IPython global ChangeLog file.

# 03.05.99 20:53 porto.ifm.uni-kiel.de
# --Started changelog.
# --make clear do what it say it does
# --added pretty output of lines from inputcache
# --Made Logger a mixin class, simplifies handling of switches
# --Added own completer class. .string<TAB> expands to last history line which
#   starts with string.
#   -The new expansion is also present with Ctrl-r from the readline library.
#    But this shows, who this can be done for other cases.
# --Added convention that all shell functions should accept a parameter_string
#   This opens the door for different behaviour for each function. @cd is a
#   good example of this.
#
# 04.05.99 12:12 porto.ifm.uni-kiel.de
# --added logfile rotation
# --added new mainloop method which freezes first the namespace
#
# 07.05.99 21:24 porto.ifm.uni-kiel.de
# --added the docreader classes. Now there is a help system.
#   -This is only a first try. Currently it's not easy to put new stuff in the
#    indices. But this is the way to go. Info would be better, but HTML is every
#    where and not everybody has an info system installed and it's not so easy to
#    change html-docs to info.
# --added global logfile option
# --there is now a hook for object inspection method pinfo needs to be provided
#   for this. Can be reached by two '??'.
#
# 08.05.99 20:51 porto.ifm.uni-kiel.de
# --added a README
# --bug in rc file. Something has changed so functions in the rc file need to
#   reference the shell and not self. Not clear if it's a bug or feature.
# --changed rc file for new behavior

#************************* end of file <iplib.py> *****************************
