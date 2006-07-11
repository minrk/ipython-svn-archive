# -*- test-case-name: ipython1.test.test_shell -*-
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
import signal

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
    capabilities.  These additional capabilities are what give IPython
    its power.  
    
    The current version of this class is meant to be a prototype that guides
    the future design of the IPython core.  This class must not use Twisted
    in any way, but it must be designed in a way that makes it easy to 
    incorporate into Twisted and hook netowrk protocols up to.  
    
    Some of the methods of this class comprise the official IPython core
    interface.  These methods must be tread safe and they must return types
    that can be easily serialized by protocols such as PB, XML-RPC and SOAP.
    Locks have been provided for making the methods thread safe, but addisional
    locks can be added as needed.
      
    Any method that is meant to be a part of the official interface must also
    be declared in the kernel.coreservice.ICoreService interface.  Eventually
    all other methods should have single leading underscores to note that they
    are not designed to be 'public.'  Currently, because this class inherits
    from code.InteractiveConsole there are many private methods w/o leading
    underscores.  The interface should be as simple as possible and methods 
    should not be added to the interface unless they really need to be there.   
    
    Note:
    
    - For now I am using methods named put/get to move objects in/out of the
      users namespace.  Originally, I was calling these methods push/pull, but
      because code.InteractiveConsole already has a push method, I had to use
      something different.  Eventually, we probably won't subclass this class
      so we can call these methods whatever we want.  So, what do we want to
      call them?
    - We need a way of running the trapping of stdout/stderr in different ways.
      We should be able to i) trap, ii) not trap at all or iii) trap and echo
      things to stdout and stderr.
    - How should errors be handled?  Should exceptions be raised?
    - What should methods that don't compute anything return?  The default of 
      None?
    """
     
    def __init__(self, locals=None, filename="<console>"):
        """Creates a new TrappingInteractiveConsole object."""
        InteractiveConsole.__init__(self,locals,filename)
        self._trap = OutputTrap(debug=0)
        self._stdin = []
        self._stdout = []
        self._stderr = []
        self._namespace_lock = threading.Lock()
        self._command_lock = threading.Lock()
        self.last_command_index = -1
        # I am using this user defined signal to interrupt the currently 
        # running command.  I am not sure if this is the best way, but
        # it is working!
        signal.signal(signal.SIGUSR1, self._handle_SIGUSR1)

    def _handle_SIGUSR1(self, signum, frame):
        """Handle the SIGUSR1 signal by printing to stderr."""
        print>>sys.stderr, "Command stopped."
        
    def _prefilter(self, line, more):
        return line

    def _trap_runlines(self, lines):
        """
        This executes the python source code, source, in the
        self.locals namespace and traps stdout and stderr.  Upon
        exiting, self.out and self.err contain the values of 
        stdout and stderr for the last executed command only.
        """
        
        # Execute the code
        self._namespace_lock.acquire()
        self._trap.flush()
        self._trap.trap()
        self._runlines(lines)
        self.last_command_index += 1
        self._trap.release()
        self._namespace_lock.release()
                
        # Save stdin, stdout and stderr to lists
        self._command_lock.acquire()
        self._stdin.append(lines)
        self._stdout.append(self._trap.out.getvalue())
        self._stderr.append(self._trap.err.getvalue())
        self._command_lock.release()

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
                more = self.push((self._prefilter(line,more)))
                # IPython's runsource returns None if there was an error
                # compiling the code.  This allows us to stop processing right
                # away, so the user gets the error message at the right place.
                if more is None:
                    break
        # final newline in case the input didn't have it, so that the code
        # actually does get executed
        if more:
            self.push('\n')

    ##################################################################
    # Methods that are a part of the official interface
    #
    # These methods should also be put in the 
    # kernel.coreservice.ICoreService interface.
    #
    # These methods must conform to certain restrictions that allow
    # them to be exposed to various network protocols:
    #
    # - As much as possible, these methods must return types that can be 
    #   serialized by PB, XML-RPC and SOAP.  None is OK.
    # - Every method must be thread safe.  There are some locks provided
    #   for this purpose, but new, specialized locks can be added to the
    #   class.
    ##################################################################
    
    # Methods for running code
    
    def execute(self, lines):
        self._trap_runlines(lines)
        return self.get_command()
        
    # Methods for working with the namespace

    def put(self, key, value):
        """Put value into locals namespace with name key.
        
        I have often called this push(), but in this case the
        InteractiveConsole class already defines a push() method that
        is different.
        """
        if not isinstance(key, str):
            raise TypeError, "Objects must be keyed by strings."
        self.update({key:value})

    def get(self, key):
        """Gets an item out of the self.locals dict by key.
        
        What should this return if the key is not defined?  Currently, I return
        a NotDefined() object.
        
        I have often called this pull().  I still like that better.
        """
        if not isinstance(key, str):
            raise TypeError, "Objects must be keyed by strings."
        self._namespace_lock.acquire()
        result = self.locals.get(key, NotDefined(key))
        self._namespace_lock.release()
        return result

    def update(self, dict_of_data):
        """Loads a dict of key value pairs into the self.locals namespace."""
        if not isinstance(dict_of_data, dict):
            raise TypeError, "update() takes a dict object."
        self._namespace_lock.acquire()
        self.locals.update(dict_of_data)
        self._namespace_lock.release()
        
    # Methods for getting stdout/stderr/stdin
           
    def reset(self):
        """Reset the InteractiveShell."""
        
        self._command_lock.acquire()        
        self._stdin = []
        self._stdout = []
        self._stderr = []
        self.last_command_index = -1
        self._command_lock.release()

        self._namespace_lock.acquire()        
        self.locals = {}
        self._namespace_lock.release()
                
    def get_command(self,i=None):
        """Get the stdin/stdout/stderr of command i."""
        
        self._command_lock.acquire()
        
        if i in range(self.last_command_index + 1):
            in_result = self._stdin[i]
            out_result = self._stdout[i]
            err_result = self._stderr[i]
            cmd_num = i
        elif i is None and self.last_command_index >= 0:
            in_result = self._stdin[self.last_command_index]
            out_result = self._stdout[self.last_command_index]
            err_result = self._stderr[self.last_command_index]
            cmd_num = self.last_command_index
        else:
            in_result = None
            out_result = None
            err_result = None
        
        self._command_lock.release()
        
        if in_result:
            return (cmd_num, in_result, out_result, err_result)
        else:
            raise IndexError, "Command with index does not exist."
            
    def get_last_command_index(self):
        """Get the index of the last command."""
        self._command_lock.acquire()
        ind = self.last_command_index
        self._command_lock.release()
        return ind
