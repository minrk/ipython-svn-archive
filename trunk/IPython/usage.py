#*****************************************************************************
#       Copyright (C) 2001 Fernando P�rez. <fperez@colorado.edu>
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

__doc__ = """
IPython -- An enhanced Interactive Python
=========================================

A Python shell with automatic history (input and output), dynamic object
introspection, easier configuration, command completion, access to the system
shell and more.

IPython can also be embedded in running programs. See EMBEDDING below.


USAGE
  ipython [options] files

If invoked with no options, it executes all the files listed in sequence and
drops you into the interpreter while still acknowledging any options you may
have set in your ipythonrc file. This behavior is different from standard
Python, which when called as python -i will only execute one file and will
ignore your configuration setup.

Please note that some of the configuration options are not available at the
command line, simply because they are not practical here. Look into your
ipythonrc configuration file for details on those. This file typically
installed in the $HOME/.ipython directory. For Windows users, $HOME resolves
to C:\\Documents and Settings\\YourUserName in most instances. In the rest of
this text, we will refer to this directory as IPYTHONDIR.


OPTIONS

All options can be abbreviated to their shortest non-ambiguous form and are
case-sensitive. One or two dashes can be used. Some options have an alternate
short form, indicated after a |.

Most options can also be set from your ipythonrc configuration file. See the
provided example for more details on what the options do. Options given at the
command line override the values set in the ipythonrc file.

All options with a no| prepended can be specified in 'no' form (-nooption
instead of -option) to turn the feature off.

 -help: print this help and exit.
 
 -no|autocall: make IPython automatically call any callable object even if
 you didn't type explicit parentheses. For example, 'str 43' becomes 'str(43)'
 automatically.

 -no|autoindent: turn automatic indentation on/off.

 -no|automagic: make magic commands automatic (without needing their first
 character to be @). Type @magic at the IPython prompt for more information.

 -no|banner: Print the initial information banner (default on).

 -cache_size|cs <n>: size of the output cache (maximum number of entries to
 hold in memory). The default is 1000, you can change it permanently in your
 config file. Setting it to 0 completely disables the caching system, and the
 minimum value accepted is 20 (if you provide a value less than 20, it is
 reset to 0 and a warning is issued) This limit is defined because otherwise
 you'll spend more time re-flushing a too small cache than working.

 -classic|cl: Gives IPython a similar feel to the classic Python prompt.

 -colors|c <scheme>: Color scheme for prompts and exception reporting.
 Currently implemented: NoColor, Linux and LightBG.

 -no|color_info: IPython can display information about objects via a set of
 functions, and optionally can use colors for this, syntax highlighting source
 code and various other elements. However, because this information is passed
 through a pager (like 'less') and many pagers get confused with color codes,
 this option is off by default. You can test it and turn it on permanently in
 your ipythonrc file if it works for you. As a reference, the 'less' pager
 supplied with Mandrake 8.2 works ok, but that in RedHat 7.2 doesn't.

 Test it and turn it on permanently if it works with your system. The magic
 function @color_info allows you to toggle this interactively for testing.

 -no|confirm_exit: set to confirm when you try to exit IPython with an EOF
 (Control-d in Unix, Control-Z/Enter in Windows). Note that using the magic
 functions @Exit or @Quit you can force a direct exit, bypassing any
 confirmation.

 -no|debug: Show information about the loading process. Very useful to pin
 down problems with your configuration files or to get details about session
 restores.

 -no|deep_reload: IPython can use the deep_reload module which reloads changes
 in modules recursively (it replaces the reload() function, so you don't need to
 change anything to use it). deep_reload() forces a full reload of modules
 whose code may have changed, which the default reload() function does not.

 When deep_reload is off, IPython will use the normal reload(), but
 deep_reload will still be available as dreload(). This feature is off by
 default [which means that you have both normal reload() and dreload()].
 
 -editor <name>: Which editor to use with the @edit command. By default,
 IPython will honor your EDITOR environment variable (if not set, vi is the
 Unix default and notepad the Windows one). Since this editor is invoked on
 the fly by IPython and is meant for editing small code snippets, you may want
 to use a small, lightweight editor here (in case your default EDITOR is
 something like Emacs).
 
 -ipythondir <name>: name of your IPython configuration directory IPYTHONDIR.
 This can also be specified through the environment variable IPYTHONDIR.
 
 -log|l: generate a log file of all input. The file is named ipython.log in
 your current directory (which prevents logs from multiple IPython sessions
 from trampling each other). You can use this to later restore a session by
 loading your logfile as a file to be executed with option -logplay (see
 below).

 -logfile|lf <name>: specify the name of your logfile.

 -logplay|lp <name>: you can replay a previous log. For restoring a session as
 close as possible to the state you left it in, use this option (don't just
 run the logfile). With -logplay, IPython will try to reconstruct the previous
 working environment in full, not just execute the commands in the logfile.

 When a session is restored, logging is automatically turned on again with the
 name of the logfile it was invoked with (it is read from the log header). So
 once you've turned logging on for a session, you can quit IPython and reload
 it as many times as you want and it will continue to log its history and
 restore from the beginning every time.

 Caveats: there are limitations in this option. The history variables _i*,_*
 and _dh don't get restored properly. In the future we will try to implement
 full session saving by writing and retrieving a 'snapshot' of the memory
 state of IPython. But our first attempts failed because of inherent
 limitations of Python's Pickle module, so this may have to wait.

 -no|messages: Print messages which IPython collects about its startup process
 (default on).

 -no|pdb: Automatically call the pdb debugger after every uncaught
 exception. If you are used to debugging using pdb, this puts you
 automatically inside of it after any call (either in IPython or in code
 called by it) which triggers an exception which goes uncaught.
 
 -no|pprint: ipython can optionally use the pprint (pretty printer) module for
 displaying results. pprint tends to give a nicer display of nested data
 structures. If you like it, you can turn it on permanently in your config
 file (default off).

 -profile|p <name>: assume that your config file is ipythonrc-<name> (looks in
 current dir first, then in IPYTHONDIR). This is a quick way to keep and load
 multiple config files for different tasks, especially if you use the include
 option of config files. You can keep a basic IPYTHONDIR/ipythonrc file and
 then have other 'profiles' which include this one and load extra things for
 particular tasks. For example:

   1) $HOME/.ipython/ipythonrc : load basic things you always want.
   2) $HOME/.ipython/ipythonrc-math : load (1) and basic math-related modules.
   3) $HOME/.ipython/ipythonrc-numeric : load (1) and Numeric and plotting
   modules.

 Since it is possible to create an endless loop by having circular file
 inclusions, IPython will stop if it reaches 15 recursive inclusions.

 -prompt_in1|pi1 <string>: Specify the string used for input prompts. Note
 that if you are using numbered prompts, the number is represented with a '%n'
 in the string. Don't forget to quote strings with spaces embedded in
 them. Default: 'In [%n]:'
 
 -prompt_in2|pi2 <string>: Similar to the previous option, but used for the
 continuation prompts. In this case, the number (%n) is replaced by as many
 dots as there are digits in the number (so you can have your continuation
 prompt aligned with your input prompt). Default: ' .%n.:' (note three spaces
 at the start for alignment with 'In [%n]')

 -prompt_out|po <string>: String used for output prompts, also uses numbers
 like prompt_in1. Default: 'Out[%n]:'

 -quick: start in bare bones mode (no config file loaded).

 -rcfile <name>: name of your IPython resource configuration file. Normally
 IPython loads ipythonrc (from current directory) or IPYTHONDIR/ipythonrc.

 If the loading of your config file fails, IPython starts with a bare bones
 configuration (no modules loaded at all).

 -no|readline: use the readline library, which is needed to support name
 completion and command history, among other things. It is enabled by default,
 but may cause problems for users of X/Emacs in Python comint or shell
 buffers.

 Note that emacs 'eterm' buffers (opened with M-x term) support IPython's
 readline and syntax coloring fine, only 'emacs' (M-x shell and C-c !) buffers
 do not.

 -screen_length|sl <n>: number of lines of your screen. This is used to
 control printing of very long strings. Strings longer than this number of
 lines will be sent through a pager instead of directly printed.

 The default value for this is 0, which means IPython will auto-detect your
 screen size every time it needs to print certain potentially long strings
 (this doesn't change the behavior of the 'print' keyword, it's only triggered
 internally). If for some reason this isn't working well (it needs curses
 support), specify it yourself. Otherwise don't change the default.

 -separate_in|si <string>: separator before input prompts. Default: '\\n'

 -separate_out|so <string>: separator before output prompts. Default: nothing.

 -separate_out2|so2 <string>: separator after output prompts. Default: nothing.

 For these three options, use the value 0 to specify no separator.

 -nosep: shorthand for '-SeparateIn 0 -SeparateOut 0 -SeparateOut2 0'. Simply
 removes all input/output separators.

 -upgrade: allows you to upgrade your IPYTHONDIR configuration when you
 install a new version of IPython. Since new versions may include new command
 line options or example files, this copies updated ipythonrc-type
 files. However, it backs up (with a .old extension) all files which it
 overwrites so that you can merge back any customizations you might have in
 your personal files.

 -Version: print version information and exit.

 -xmode <modename>. Mode for exception reporting.

  Valid modes: Plain, Context and Verbose.

  Plain: similar to python's normal traceback printing.

  Context: prints 5 lines of context source code around each line in the traceback.

  Verbose: similar to Context, but additionally prints the variables currently
  visible where the exception happened (shortening their strings if too
  long). This can potentially be very slow, if you happen to have a huge data
  structure whose string representation is complex to compute. Your computer
  may appear to freeze for a while with cpu usage at 100%. If this occurs, you
  can cancel the traceback with Ctrl-C (maybe hitting it more than once).


EMBEDDING

It is possible to start an IPython instance *inside* your own Python
programs. In your IPYTHONDIR sample files are provided illustrating how to do
this.

This feature allows you to evaluate dynamically the state of your code,
operate with your variables, analyze them, etc. Note however that any changes
you make to values while in the shell do NOT propagate back to the running
code, so it is safe to modify your values because you won't break your code in
bizarre ways by doing so.
"""

cmd_line_usage = __doc__

#---------------------------------------------------------------------------
interactive_usage = """
IPython -- An enhanced Interactive Python
=========================================

IPython offers a combination of convenient shell features, special commands
and a history mechanism for both input (command history) and output (results
caching, similar to Mathematica). It is intended to be a fully compatible
replacement for the standard Python interpreter, while offering vastly
improved functionality and flexibility.

At your system command line, type 'ipython -help' to see the command line
options available. This document only describes interactive features.

Warning: IPython relies on the existence of a global variable called __IP which
controls the shell itself. If you redefine __IP to anything, bizarre behavior
will quickly occur.

MAIN FEATURES

* Access to the standard Python help. As of Python 2.1, a help system is
  available with access to object docstrings and the Python manuals. Simply
  type 'help' (no quotes) to access it.

* Magic commands: type @magic for information on the magic subsystem.

* System command aliases, via the @alias command or the ipythonrc config file.

* Dynamic object information:

  Typing ?word or word? prints detailed information about an object.  If
  certain strings in the object are too long (docstrings, code, etc.) they get
  snipped in the center for brevity.

  Typing ??word or word?? gives access to the full information without
  snipping long strings. Long strings are sent to the screen through the less
  pager if longer than the screen, printed otherwise.

  The ?/?? system gives access to the full source code for any object (if
  available), shows function prototypes and other useful information.

  If you just want to see an object's docstring, type '@pdoc object' (without
  quotes, and without @ if you have automagic on).

  Both @pdoc and ?/?? give you access to documentation even on things which are
  not explicitely defined. Try for example typing {}.get? or after import os,
  type os.path.abspath??. The magic functions @pdef, @source and @file operate
  similarly.

* Completion in the local namespace, by typing TAB at the prompt.

  At any time, hitting tab will complete any available python commands or
  variable names, and show you a list of the possible completions if there's
  no unambiguous one. It will also complete filenames in the current directory.

  This feature requires the readline and rlcomplete modules, so it won't work
  if your Python lacks readline support (such as under Windows).

* Search previous command history in two ways (also requires readline):

  - Start typing, and then use Ctrl-p (previous,up) and Ctrl-n (next,down) to
  search through only the history items that match what you've typed so
  far. If you use Ctrl-p/Ctrl-n at a blank prompt, they just behave like
  normal arrow keys.

  - Hit Ctrl-r: opens a search prompt. Begin typing and the system searches
  your history for lines that match what you've typed so far, completing as
  much as it can.

* Persistent command history across sessions (readline required).

* Logging of input with the ability to save and restore a working session.
  
* System escape with !. Typing !ls will run 'ls' in the current directory.

* The reload command does a 'deep' reload of a module: changes made to the
  module since you imported will actually be available without having to exit.

* Verbose and colored exception traceback printouts. See the magic xmode and
  xcolor functions for details (just type @magic).

* Input caching system:

  IPython offers numbered prompts (In/Out) with input and output caching. All
  input is saved and can be retrieved as variables (besides the usual arrow
  key recall).

  The following GLOBAL variables always exist (so don't overwrite them!):
  _i: stores previous input.
  _ii: next previous.
  _iii: next-next previous.
  _ih : a list of all input _ih[n] is the input from line n.

  Additionally, global variables named _i<n> are dynamically created (<n>
  being the prompt counter), such that _i<n> == _ih[<n>]

  For example, what you typed at prompt 14 is available as _i14 and _ih[14].

  You can create macros which contain multiple input lines from this history,
  for later re-execution, with the @macro function.

  The history function @hist allows you to see any part of your input history
  by printing a range of the _i variables. Note that inputs which contain
  magic functions (@) appear in the history with a prepended comment. This is
  because they aren't really valid Python code, so you can't exec them.

* Output caching system:

  For output that is returned from actions, a system similar to the input
  cache exists but using _ instead of _i. Only actions that produce a result
  (NOT assignments, for example) are cached. If you are familiar with
  Mathematica, IPython's _ variables behave exactly like Mathematica's %
  variables.

  The following GLOBAL variables always exist (so don't overwrite them!):
  _ (one underscore): previous output.
  __ (two underscores): next previous.
  ___ (three underscores): next-next previous.

  Global variables named _<n> are dynamically created (<n> being the prompt
  counter), such that the result of output <n> is always available as _<n>.

  Finally, a global dictionary named _oh exists with entries for all lines
  which generated output.

* Directory history:

  Your history of visited directories is kept in the global list _dh, and the
  magic @cd command can be used to go to any entry in that list.

* Auto-parentheses and auto-quotes (adapted from Nathan Gray's LazyPython)

    1. Auto-parentheses
        Callable objects (i.e. functions, methods, etc) can be invoked like
        this (notice the commas between the arguments):
            >>> callable_ob arg1, arg2, arg3
        and the input will be translated to this:
            --> callable_ob(arg1, arg2, arg3)
        You can force auto-parentheses by using '/' as the first character
        of a line.  For example:
            >>> /globals             # becomes 'globals()'
        Note that the '/' MUST be the first character on the line!  This
        won't work:
            >>> print /globals    # syntax error
            
        In most cases the automatic algorithm should work, so you should
        rarely need to explicitly invoke /. One notable exception is if you
        are trying to call a function with a list of tuples as arguments (the
        parenthesis will confuse IPython):
            In [1]: zip (1,2,3),(4,5,6)  # won't work
        but this will work:
            In [2]: /zip (1,2,3),(4,5,6)
            ------> zip ((1,2,3),(4,5,6))
            Out[2]= [(1, 4), (2, 5), (3, 6)]        

    2. Auto-Quoting
        You can force auto-quoting of a function's arguments by using ',' as
        the first character of a line.  For example:
            >>> ,my_function /home/me   # becomes my_function("/home/me")
        Note that the ',' MUST be the first character on the line!  This
        won't work:
            >>> x = ,my_function /home/me    # syntax error

  Notes on usage of these two features:
  
    1.  IPython tells you that it has altered your command line by
        displaying the new command line preceded by -->.  e.g.:
            In [18]: callable list
            -------> callable (list) 

    2.  Whitespace is more important than usual (even for Python!)
        Arguments to auto-quote functions cannot have embedded whitespace.
        
            In [21]: ,string.split a b
            -------> string.split ("a", "b")
            Out[21]= ['a']       # probably not what you wanted

            In [22]: string.split 'a b'
            -------> string.split ('a b')
            Out[22]= ['a', 'b']  # quote explicitly and it works.
"""
