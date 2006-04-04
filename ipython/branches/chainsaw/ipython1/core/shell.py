"""
The core IPython Shell
"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import time
import sys
import threading

from code import InteractiveConsole
from StringIO import StringIO

from IPython.OutputTrap import OutputTrap

try:
    from ipython1.kernel1p.kernelerror import NotDefined
except ImportError:
    print "ipython1 needs to be in your PYTHONPATH"

class InteractiveShell(InteractiveConsole):
    """The Basic IPython Shell class.  
    
    This class provides the basic capabilities of IPython.  Currently
    this class does not do anything IPython specific.  That is, it is
    just a python shell.
    
    It is modelled on code.InteractiveConsole, but adds additional
    capabilities:
    
    - Trapping of input, output and stderr
    - Working with the locals namespace

    Questions:
    
    - Do we use push/pull or put/get?
    """
     
    def __init__(self, locals=None, filename="<console>"):
        """Creates a new TrappingInteractiveConsole object."""
        InteractiveConsole.__init__(self,locals,filename)
        self._trap = OutputTrap(debug=0)
        self._stdin = []
        self._stdout = []
        self._stderr = []
        self._datalock = threading.Lock()
        self._inouterr_lock = threading.Lock()

    def prefilter(self, line, more):
        return line

    def runlines(self, lines):
        """
        This executes the python source code, source, in the
        self.locals namespace and traps stdout and stderr.  Upon
        exiting, self.out and self.err contain the values of 
        stdout and stderr for the last executed command only.
        """
        
        # Execute the code
        self._datalock.acquire()
        self._trap.flush()
        self._trap.trap()
        self._runlines(lines)
        self._trap.release()
        self._datalock.release()
                
        # Save stdin, stdout and stderr to lists
        self._inouterr_lock.acquire()
        self._stdin.append(lines)
        self._stdout.append(self._trap.out.getvalue())
        self._stderr.append(self._trap.err.getvalue())
        self._inouterr_lock.release()

    # Lifted from iplib.InteractiveShell
    def _runlines(self,lines):
        """Run a string of one or more lines of source.

        This method is capable of running a string containing multiple source
        lines, as if they had been entered at the IPython prompt.  Since it
        exposes IPython's processing machinery, the given strings can contain
        magic calls (%magic), special shell access (!cmd), etc."""

        # We must start with a clean buffer, in case this is run from an
        # interactive IPython session (via a magic, for example).
        self.resetbuffer()
        lines = lines.split('\n')
        more = 0
        for line in lines:
            # skip blank lines so we don't mess up the prompt counter, but do
            # NOT skip even a blank line if we are in a code block (more is
            # true)
            if line or more:
                more = self.push((self.prefilter(line,more)))
                # IPython's runsource returns None if there was an error
                # compiling the code.  This allows us to stop processing right
                # away, so the user gets the error message at the right place.
                if more is None:
                    break
        # final newline in case the input didn't have it, so that the code
        # actually does get executed
        if more:
            self.push('\n')

    def update(self,dict_of_data):
        """Loads a dictionary of key value pairs into the self.locals 
        namespace and traps stdout and stderr."""
        self._datalock.acquire()
        self.locals.update(dict_of_data)
        self._datalock.release()
        return

    ###################################################
    # Methods that are a part of the official interface
    ###################################################
    
    # Methods for running code
    
    def execute(self, lines):
        return self.runlines(lines)

    # Methods for working with the namespace

    def put(self, key, value):
        """Put value into locals namespace with name key.
        
        I have often called this push(), but in this case the
        InteractiveConsole class already defines a push() method that
        is different.
        """
        self.update({key:value})

    def get(self,key):
        """Gets an item out of the self.locals dict by key.
        
        I have often called this pull().
        """
        self._datalock.acquire()
        result = self.locals.get(key, NotDefined(key))
        self._datalock.release()
        return result
                
    # Methods for getting stdout/stderr/stdin
                
    def get_command(self,i=-1):
        """Get the stdin/stdout/stderr of command i."""
        
        self._inouterr_lock.acquire()
        
        if i in range(len(self._stdin)):
            in_result = self._stdin[i]
            out_result = self._stdout[i]
            err_result = self._stderr[i]
        elif i==-1 and len(self._stdin) != 0:
            in_result = self._stdin[-1]
            out_result = self._stdout[-1]
            err_result = self._stderr[-1]
        else:
            in_result = None
            out_result = None
            err_result = None
        
        self._inouterr_lock.release()
        
        if in_result:
            return (in_result, out_result, err_result)
        else:
            return None

