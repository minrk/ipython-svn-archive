# -*- coding: iso-8859-1 -*-
"""IPython Shell classes.

$Id$"""

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
import Release
__version__ = Release.version
__date__    = Release.date
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = Release.license

# Code begins
import __main__
import __builtin__
import sys
import os
import code
import threading

import IPython
from ipmaker import make_IPython
from genutils import Term,warn,error
from Struct import Struct
from Magic import Magic
import ultraTB

#-----------------------------------------------------------------------------
# This class is trivial now, but I want to have it in to publish a clean
# interface. Later when the internals are reorganized, code that uses this
# shouldn't have to change.

class IPShell:
    """Create an IPython instance."""
    
    def __init__(self,argv=None,user_ns=None,debug=0):
        self.IP = make_IPython(argv,user_ns=user_ns,debug=debug)

    def mainloop(self,sys_exit=0):
        self.IP.mainloop()
        if sys_exit:
            sys.exit()

# alias for backwards compatibility
IPythonShell = IPShell

#-----------------------------------------------------------------------------
class IPShellEmbed:
    """Allow embedding an IPython shell into a running program.

    Instances of this class are callable, with the __call__ method being an
    alias to the embed() method of an InteractiveShell instance.

    Usage (see also the example-embed.py file for a running example):

    IPShell = IPythonShellEmbed([argv,banner,exit_msg,rc_override])

    - argv: list containing valid command-line options for IPython, as they
    would appear in sys.argv.

    For example, the following command-line options:

      $ ipython -prompt_in1 'Input <\\#>' -colors LightBG

    would be passed in the argv list as:

      ['-prompt_in1','Input <\\#>','-colors','LightBG']

    - banner: string which gets printed every time the interpreter starts.

    - exit_msg: string which gets printed every time the interpreter exits.

    - rc_override: a dict or Struct of configuration options such as those
    used by IPython. These options are read from your ~/.ipython/ipythonrc
    file when the Shell object is created. Passing an explicit rc_override
    dict with any options you want allows you to override those values at
    creation time without having to modify the file. This way you can create
    embeddable instances configured in any way you want without editing any
    global files (thus keeping your interactive IPython configuration
    unchanged).

    Then the IPShell instance can be called anywhere inside your code:
    
    IPShell(local_ns=None,header='') -> Opens up an IPython shell.

    - local_ns: local namespace. When IPShell is called inside a function, the
    call MUST be IPShell(vars()) so that IPShell knows about local
    variables. At the top-level of a program it may be omitted, it will
    default to __main__.__dict__.

    - header: string printed by the IPython shell upon startup. This can let
    you know where in your code you are when dropping into the shell. Note
    that 'banner' gets prepended to all calls, so header is used for
    location-specific information.

    When the IPython shell is exited with Ctrl-D, normal program execution
    resumes.

    This functionality was inspired by a posting on comp.lang.python by cmkl
    <cmkleffner@gmx.de> on Dec. 06/01 concerning similar uses of pyrepl, and
    by the IDL stop/continue commands."""

    def __init__(self,argv=None,banner='',exit_msg=None,rc_override=None):
        """Note that argv here is a string, NOT a list."""
        self.set_banner(banner)
        self.set_exit_msg(exit_msg)
        self.set_dummy_mode(0)

        # sys.displayhook is a global, we need to save the user's original
        # Don't rely on __displayhook__, as the user may have changed that.
        self.sys_displayhook_ori = sys.displayhook

        # save readline completer status
        try:
            #print 'Save completer',sys.ipcompleter  # dbg
            self.sys_ipcompleter_ori = sys.ipcompleter
        except:
            pass # not nested with IPython
        
        # FIXME. Passing user_ns breaks namespace handling.
        #self.IP = make_IPython(argv,user_ns=__main__.__dict__)
        self.IP = make_IPython(argv,rc_override=rc_override)

        self.IP.name_space_init()
        # mark this as an embedded instance so we know if we get a crash post-mortem
        self.IP.rc.embedded = 1
        # copy our own displayhook also
        self.sys_displayhook_embed = sys.displayhook
        # and leave the system's display hook clean
        sys.displayhook = self.sys_displayhook_ori
        # don't use the ipython crash handler so that user exceptions aren't trapped
        sys.excepthook = ultraTB.FormattedTB(color_scheme = self.IP.rc.colors,
                                             mode = self.IP.rc.xmode,
                                             call_pdb = self.IP.rc.pdb)
        self.restore_system_completer()

    def restore_system_completer(self):
        """Restores the readline completer which was in place.

        This allows embedded IPython within IPython not to disrupt the
        parent's completion.
        """
        
        try:
            self.IP.readline.set_completer(self.sys_ipcompleter_ori)
            sys.ipcompleter = self.sys_ipcompleter_ori
        except:
            pass

    def __call__(self,header='',local_ns=None,global_ns=None,dummy=None):
        """Activate the interactive interpreter.

        __call__(self,header='',local_ns=None,global_ns,dummy=None) -> Start
        the interpreter shell with the given local and global namespaces, and
        optionally print a header string at startup.

        The shell can be globally activated/deactivated using the
        set/get_dummy_mode methods. This allows you to turn off a shell used
        for debugging globally.

        However, *each* time you call the shell you can override the current
        state of dummy_mode with the optional keyword parameter 'dummy'. For
        example, if you set dummy mode on with IPShell.set_dummy_mode(1), you
        can still have a specific call work by making it as IPShell(dummy=0).

        The optional keyword parameter dummy controls whether the call
        actually does anything.  """

        # Allow the dummy parameter to override the global __dummy_mode
        if dummy or (dummy != 0 and self.__dummy_mode):
            return

        # Set global subsystems (display,completions) to our values
        sys.displayhook = self.sys_displayhook_embed
        if self.IP.has_readline:
            self.IP.readline.set_completer(self.IP.Completer.complete)

        if self.banner and header:
            format = '%s\n%s\n'
        else:
            format = '%s%s\n'
        banner =  format % (self.banner,header)

        # Call the embedding code with a stack depth of 1 so it can skip over
        # our call and get the original caller's namespaces.
        self.IP.embed_mainloop(banner,local_ns,global_ns,stack_depth=1)

        if self.exit_msg:
            print self.exit_msg
            
        # Restore global systems (display, completion)
        sys.displayhook = self.sys_displayhook_ori
        self.restore_system_completer()
    
    def set_dummy_mode(self,dummy):
        """Sets the embeddable shell's dummy mode parameter.

        set_dummy_mode(dummy): dummy = 0 or 1.

        This parameter is persistent and makes calls to the embeddable shell
        silently return without performing any action. This allows you to
        globally activate or deactivate a shell you're using with a single call.

        If you need to manually"""

        if dummy not in [0,1]:
            raise ValueError,'dummy parameter must be 0 or 1'
        self.__dummy_mode = dummy

    def get_dummy_mode(self):
        """Return the current value of the dummy mode parameter.
        """
        return self.__dummy_mode
    
    def set_banner(self,banner):
        """Sets the global banner.

        This banner gets prepended to every header printed when the shell
        instance is called."""

        self.banner = banner

    def set_exit_msg(self,exit_msg):
        """Sets the global exit_msg.

        This exit message gets printed upon exiting every time the embedded
        shell is called. It is None by default. """

        self.exit_msg = exit_msg

# alias for backwards compatibility
IPythonShellEmbed = IPShellEmbed

#-----------------------------------------------------------------------------
class MTInteractiveShell(IPython.iplib.InteractiveShell):
    """Simple multi-threaded shell."""

    # Threading strategy taken from:
    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/65109, by Brian
    # McErlean and John Finlay.  Modified with corrections by Antoon Pardon,
    # from the pygtk mailing list, to avoid lockups with system calls.

    def __init__(self,name,usage=None,rc=Struct(opts=None,args=None),
                 user_ns = None, banner2='',**kw):
        """Similar to the normal InteractiveShell, but with threading control"""
        
        IPython.iplib.InteractiveShell.__init__(self,name,usage,rc,user_ns,banner2)

        # Object variable to store code object waiting execution.  No need to
        # use a Queue here, since it's a single item which gets cleared once run.
        self.code_to_run = None
        self.parent_runcode = lambda obj: \
                              IPython.iplib.InteractiveShell.runcode(self,obj)

        # Locking control variable
        self.ready = threading.Condition()

        # Stuff to do at closing time
        self._kill = False
        on_kill = kw.get('on_kill')
        if on_kill is None:
            on_kill = []
        # Check that all things to kill are callable:
        for t in on_kill:
            if not callable(t):
                raise TypeError,'on_kill must be a list of callables'
        self.on_kill = on_kill
        
    def runsource(self, source, filename="<input>", symbol="single"):
        """Compile and run some source in the interpreter.

        Modified version of code.py's runsource(), to handle threading issues.
        See the original for full docstring details."""
        
        try:
            code = self.compile(source, filename, symbol)
        except (OverflowError, SyntaxError, ValueError):
            # Case 1
            self.showsyntaxerror(filename)
            return False

        if code is None:
            # Case 2
            return True

        # Case 3
        # Store code in self, so the execution thread can handle it
        self.ready.acquire()
        self.code_to_run = code
        self.ready.wait()  # Wait until processed in timeout interval
        self.ready.release()

        return False

    def runcode(self):
        """Execute a code object.

        Multithreaded wrapper around IPython's runcode()."""

        # lock thread-protected stuff
        self.ready.acquire()
        if self._kill:
            print >>Term.cout, 'Closing threads...',
            Term.cout.flush()
            for tokill in self.on_kill:
                tokill()
            print >>Term.cout, 'Done.'

        # Run pending code by calling parent class
        if self.code_to_run is not None:
            self.ready.notify()
            self.parent_runcode(self.code_to_run)

        # Flush out code object which has been run
        self.code_to_run = None
        # We're done with thread-protected variables
        self.ready.release()
        # This MUST return true for gtk threading to work
        return True

    def kill (self):
        """Kill the thread, returning when it has been shut down."""
        self.ready.acquire()
        self._kill = True
        self.ready.release()

class MatplotlibShell(MTInteractiveShell):
    """Multithreaded shell, modified to handle matplotlib scripts."""

    # This code was co-developed with John Hunter, matplotlib's author.

    def __init__(self,name,usage=None,rc=Struct(opts=None,args=None),
                 user_ns = None, **kw):
        
        # Initialize matplotlib to interactive mode always
        import matplotlib
        matplotlib.interactive(True)

        # we'll handle the mainloop, tell show not to
        from matplotlib.backends import show 
        show._needmain = False

        # This must be imported last in the matplotlib series, after
        # backend/interactivity choices have been made
        import matplotlib.matlab as matlab
        self.matplotlib = matplotlib

        # Build a user namespace initialized with matplotlib/matlab features.
        user_ns = {'__name__':'__main__',
                   '__builtins__' : __builtin__,
                   name:self,
                   }
        exec "import matplotlib.matlab as matlab" in user_ns
        exec "from matplotlib.matlab import *" in user_ns

        # Add matplotlib info to banner
        b2= """\nWelcome to pylab, a matplotlib-based Python environment.
help(matlab)   -> help on matlab compatible commands from matplotlib.
help(plotting) -> help on plotting commands.
"""
        # Initialize parent class
        MTInteractiveShell.__init__(self,name,usage,rc,user_ns,banner2=b2,**kw)

    def mplot_exec(self,fname,*where):
        """Execute a matplotlib script."""

        #print '*** Matplotlib runner ***' # dbg
        # turn off rendering until end of script
        isInteractive = self.matplotlib.rcParams['interactive']
        self.matplotlib.interactive(False)
        self.safe_execfile(fname,*where)
        self.matplotlib.interactive(isInteractive)
        self.matplotlib.matlab.draw()
        
    def magic_run(self,parameter_s=''):
        """Modified @run for Matplotlib"""
        Magic.magic_run(self,parameter_s,runner=self.mplot_exec)

#-----------------------------------------------------------------------------
# The IPShell* classes below are the ones meant to be run by external code as
# IPython instances.  Note that unless a specific threading strategy is
# desired, the factory function start() below should be used instead (it
# selects the proper threaded class).

class IPShellGTK(threading.Thread):
    """Run a gtk mainloop() in a separate thread.
    
    Python commands can be passed to the thread where they will be executed.
    This is implemented by periodically checking for passed code using a
    GTK timeout callback."""
    
    TIMEOUT = 100 # Millisecond interval between timeouts.

    def __init__(self,argv=None,user_ns=None,debug=0,
                 shell_class=MTInteractiveShell):

        import pygtk
        pygtk.require("2.0")
        import gtk

        self.gtk = gtk
        self.IP = make_IPython(argv,user_ns=user_ns,debug=debug,
                               shell_class=shell_class,
                               on_kill=[self.gtk.mainquit])
        threading.Thread.__init__(self)

    def run(self):
        self.IP.mainloop()
        self.IP.kill()

    def mainloop(self):
        self.start()
        self.gtk.timeout_add(self.TIMEOUT, self.IP.runcode)
        try:
            if self.gtk.gtk_version[0] >= 2:
                self.gtk.threads_init()
        except AttributeError:
            pass
        self.gtk.mainloop()
        self.join()

class IPShellWX(threading.Thread):
    """Run a wx mainloop() in a separate thread.
    
    Python commands can be passed to the thread where they will be executed.
    This is implemented by periodically checking for passed code using a
    GTK timeout callback."""
    
    TIMEOUT = 100 # Millisecond interval between timeouts.

    def __init__(self,argv=None,user_ns=None,debug=0,
                 shell_class=MTInteractiveShell):

        import wxPython.wx as wx

        threading.Thread.__init__(self)
        self.wx = wx
        self.IP = make_IPython(argv,user_ns=user_ns,debug=debug,
                               shell_class=shell_class,
                               on_kill=[self.wxexit])
        self.app = None

    def wxexit(self, *args):
        if self.app is not None:
            self.app.agent.timer.Stop()
            self.app.ExitMainLoop()

    def run(self):
        self.IP.mainloop()
        self.IP.kill()

    def mainloop(self):
        
        self.start()

        class TimerAgent(self.wx.wxMiniFrame):
            wx = self.wx
            IP = self.IP
            def __init__(self, parent, interval):
                style = self.wx.wxDEFAULT_FRAME_STYLE | self.wx.wxTINY_CAPTION_HORIZ
                self.wx.wxMiniFrame.__init__(self, parent, -1, ' ', pos=(200, 200),
                                             size=(100, 100),style=style)
                self.Show(False)
                self.interval = interval
                self.timerId = self.wx.wxNewId()                                

            def StartWork(self):
                self.timer = self.wx.wxTimer(self, self.timerId)
                self.wx.EVT_TIMER(self,  self.timerId, self.OnTimer)
                self.timer.Start(self.interval)

            def OnTimer(self, event):
                self.IP.runcode()

        class App(self.wx.wxApp):
            wx = self.wx
            def OnInit(self):
                'Create the main window and insert the custom frame'
                self.agent = TimerAgent(None, 100)
                self.agent.Show(self.wx.false)
                self.agent.StartWork()

                return self.wx.true
        
        self.app = App()
        self.app.MainLoop()
        self.join()

class IPShellMatplotlibGTK(IPShellGTK):
    """Subclass IPShellGTK with MatplotlibShell as the internal shell.

    Having this on a separate class simplifies the external driver code."""
    
    def __init__(self,argv=None,user_ns=None,debug=0):
        IPShellGTK.__init__(self,argv,user_ns,debug,shell_class=MatplotlibShell)

class IPShellMatplotlibWX(IPShellWX):
    """Subclass IPShellWX with MatplotlibShell as the internal shell.

    Having this on a separate class simplifies the external driver code."""
    
    def __init__(self,argv=None,user_ns=None,debug=0):
        IPShellWX.__init__(self,argv,user_ns,debug,shell_class=MatplotlibShell)

#-----------------------------------------------------------------------------
# Factory functions to actually start the proper thread-aware shell
def _matplotlib_shell_class():
    """Factory function to handle shell class selection for matplotlib.

    The proper shell class to use depends on the matplotlib backend, since
    each backend requires a different threading strategy."""

    try:
        import matplotlib
    except ImportError:
        error('matplotlib could NOT be imported!  Starting normal IPython.')
        shell = IPShell
    else:
        backend = matplotlib.rcParams['backend']
        if backend.startswith('GTK'):
            shell = IPShellMatplotlibGTK
        elif backend.startswith('WX'):
            shell = IPShellMatplotlibWX
        else:
            shell = IPShell
    print 'Using %s with the %s backend.' % (shell,backend) # dbg
    return shell

# This is the one which should be called by external code.
def start():
    """Return a running shell instance, dealing with threading options.

    This is a factory function which will instantiate the proper IPython shell
    based on the user's threading choice.  Such a selector is needed because
    different GUI toolkits require different thread handling details."""
    
    # Simple sys.argv hack to extract the threading option.
    if len(sys.argv) > 1:
        arg1 = sys.argv[1]
        if arg1.endswith('-gthread'):
            shell = IPShellGTK
        elif arg1.endswith('-wthread'):
            shell = IPShellWX
        elif arg1.endswith('-pylab'):
            shell = _matplotlib_shell_class()
        else:
            shell = IPShell
    else:
        shell = IPShell
    return shell()

#************************ End of file <Shell.py> ***************************
