# -*- coding: iso-8859-1 -*-
"""Modified input prompt for executing files.

We define a special input line filter to allow typing lines which begin with
'~', '/' or '.'. If one of those strings is encountered, it is automatically
executed.

All other input is processed normally."""

#*****************************************************************************
#       Copyright (C) 2001 Fernando Perez. <fperez@colorado.edu>
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

__author__ = 'W.J. van der Laan <gnufnork@hetdigitalegat.nl>, '\
             'Fernando Perez. <fperez@colorado.edu> '
__version__= '0.1.0'
__license__= 'LGPL'
__date__   = 'Tue Jan 27 18:56:01 CET 2004'

def prefilter_shell(self,line,continuation):
    """Alternate prefilter, modified for shell-like functionality.

    - Execute all lines beginning with '~', '/' or '.'
    - $var=cmd <=> @sc var=cmd
    - $$var=cmd <=> @sc -l var=cmd
    """

    if line:
        l0 = line[0]
        if l0 in '~/.':
            return self._prefilter("!%s"%line,continuation)
        elif l0=='$':
            lrest = line[1:]
            if lrest.startswith('$'):
                # $$var=cmd <=> @sc -l var=cmd
                return self._prefilter("@sc -l %s" % lrest[1:],continuation)
            else:
                # $var=cmd <=> @sc var=cmd
                return self._prefilter("@sc %s" % lrest,continuation)
        else:
            return self._prefilter(line,continuation)
    else:
        return self._prefilter(line,continuation)

# Rebind this to be the new IPython prefilter:
from IPython.iplib import InteractiveShell
InteractiveShell.prefilter = prefilter_shell

# Provide pysh and further shell-oriented services
import os,sys,shutil
from IPython.genutils import system,shell,getoutput,getoutputerror

# Short aliases for getting shell output as a string and a list
sout = getoutput
lout = lambda cmd: getoutput(cmd,split=1)

def pysh():

    """Pysh is a set of modules and extensions to IPython which make shell-like
    usage with Python syntax more convenient.  Keep in mind that pysh is NOT a
    full-blown shell, so don't try to make it your /etc/passwd entry!
    
    In particular, it has no job control, so if you type Ctrl-Z (under Unix),
    you'll suspend pysh itself, not the process you just started.

    Since pysh is really nothing but a customized IPython, you should
    familiarize yourself with IPython's features.  This brief help mainly
    documents areas in which pysh differs from the normal IPython.

    ALIASES
    -------
    All of your $PATH has been loaded as IPython aliases, so you should be
    able to type any normal system command and have it executed.  See @alias? 
    and @unalias? for details on the alias facilities.

    SPECIAL SYNTAX
    --------------
    Any lines which begin with '~', '/' and '.' will be executed as shell
    commands instead of as Python code. The special escapes below are also
    recognized.  !cmd is valid in single or multi-line input, all others are
    only valid in single-line input:

    !cmd      - pass 'cmd' directly to the shell
    !!cmd     - execute 'cmd' and return output as a list (split on '\\n')
    $var=cmd  - capture output of cmd into var, as a string
    $$var=cmd - capture output of cmd into var, as a list (split on '\\n')

    The $/$$ syntaxes make Python variables from system output, which you can
    later use for further scripting.  The converse is also possible: when
    executing an alias or calling to the system via !/!!, you can expand any
    python variable or expression by prepending it with $.  Full details of
    the allowed syntax can be found in Python's PEP 215.

    A few brief examples will illustrate these:

        fperez[~/test]|3> !ls *s.py
        scopes.py  strings.py

    ls is an internal alias, so there's no need to use !:
        fperez[~/test]|4> ls *s.py
        scopes.py*  strings.py

    !!ls will return the output into a Python variable:
        fperez[~/test]|5> !!ls *s.py
                      <5> ['scopes.py', 'strings.py']
        fperez[~/test]|6> print _5
        ['scopes.py', 'strings.py']

    $ and $$ allow direct capture to named variables:
        fperez[~/test]|7> $astr = ls *s.py
        fperez[~/test]|8> astr
                      <8> 'scopes.py\\nstrings.py'
        fperez[~/test]|9> $$alist = ls *s.py
        fperez[~/test]|10> alist
                      <10> ['scopes.py', 'strings.py']

    alist is now a normal python list you can loop over.  Using $ will expand
    back the python values when alias calls are made:
        fperez[~/test]|11> for f in alist:
                      |..>     print 'file',f,
                      |..>     wc -l $f
                      |..>
        file scopes.py     13 scopes.py
        file strings.py      4 strings.py

    IPython's input history handling is still active, which allows you to
    rerun a single block of multi-line input by simply using exec:    
        fperez[~/test]|12> $$alist = ls *.eps
        fperez[~/test]|13> exec _i11
        file image2.eps    921 image2.eps
        file image.eps    921 image.eps

    While these are new special-case syntaxes, they are designed to allow very
    efficient use of the shell with minimal typing.  At an interactive shell
    prompt, conciseness of expression wins over readability.

    USEFUL FUNCTIONS AND MODULES
    ----------------------------
    The os, sys and shutil modules from the Python standard library are
    automatically loaded.  Some additional functions, useful for shell usage,
    are listed below.  You can request more help about them with '?'.

    shell   - execute a command in the underlying system shell    
    system  - like shell(), but return the exit status of the command
    sout    - capture the output of a command as a string
    lout    - capture the output of a command as a list (split on '\\n')
    getoutputerror - capture (output,error) of a shell command

    sout/lout are the functional equivalents of $/$$.  They are provided to
    allow you to capture system output in the middle of true python code,
    function definitions, etc (where $ and $$ are invalid).

    DIRECTORY MANAGEMENT
    --------------------
    Since each command passed by pysh to the underlying system is executed in
    a shell which exits immediately, you can NOT use !cd to navigate the
    filesystem.

    Pysh provides its own builtin '@cd' magic command to move in the
    filesystem (the @ is not required with automagic on).  It also maintains a
    list of visited directories (use @dhist to see it) and allows direct
    switching to any of them.  Type 'cd?' for more details.

    @pushd, @popd and @dirs are provided for directory stack handling.
    """
    pass

# Clean up the namespace.
del InteractiveShell,prefilter_shell
