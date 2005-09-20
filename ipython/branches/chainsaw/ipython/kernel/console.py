"""Classes that derive from code.InteractiveConsole.

This module adds additional functionality, such as output trapping,
thread safety and queues to the classes in the builtin python module code.py.

Classes:

TrappingInteractiveConsole -- InteractiveConsole that traps stdout and stderr
QueuedInteractiveConsole   -- Multithreaded InteractiveConsole with a queue
"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import Queue
import threading
import time
import sys

from code import InteractiveConsole
from StringIO import StringIO

from IPython.OutputTrap import OutputTrap

from ticketedqueue import TicketedQueue

from kernelerror import NotDefined

#try:
#    from ipython.kernel.kernelerror import NotDefined
#except ImportError:
#    from kernel.kernelerror import NotDefined

class TrappingInteractiveConsole(InteractiveConsole):
    """This class subclasses code.InteractiveConsole to
    implement an InteractiveConsole that traps stdout
    and stderr.  
    
    The trapping is done by IPython.OutputTrap and the results
    of stdout and stderr and placed in self.out and self.err.
    
    In addition to overridding runsource, to implement the trapping
    I also provide an assign, which allows a dictionary of data to
    be interted into the self.locals (the running namespace)."""
     
    def __init__(self, locals=None, filename="<console>"):
        """Creates a new TrappingInteractiveConsole object."""
        InteractiveConsole.__init__(self,locals,filename)
        self._trap = OutputTrap(debug=0)
        self._stdin = []
        self._stdout = []
        self._stderr = []
        self._datalock = threading.Lock()
        self._inouterr_lock = threading.Lock()

    def runsource(self, source, filename="<input>", symbol="single"):
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
        #result = InteractiveConsole.runsource(self,source,filename,symbol)

        # Hack for multiple lines of code
        try:
            code = compile(source, filename, symbol)
        except (OverflowError, SyntaxError, ValueError):
            # Case 1
            self.showsyntaxerror(filename)
            result = None

        if code is None:
            # Case 2
            result = True

        # Case 3
        # We store the code object so that threaded shells and
        # custom exception handlers can access all this info if needed.
        # The source corresponding to this can be obtained from the
        # buffer attribute as '\n'.join(self.buffer).
        self.code_to_run = code
        # now actually execute the code object
        if self.runcode(code) == 0:
            result = False
        else:
            result = None

        self._trap.release()
        self._datalock.release()
                
        # Save stdin, stdout and stderr to lists
        self._inouterr_lock.acquire()
        self._stdin.append(source)
        self._stdout.append(self._trap.out.getvalue())
        self._stderr.append(self._trap.err.getvalue())
        self._inouterr_lock.release()

        return result
        
    def update(self,dict_of_data):
        """Loads a dictionary of key value pairs into the self.locals 
        namespace and traps stdout and stderr."""
        self._datalock.acquire()
        self.locals.update(dict_of_data)
        self._datalock.release()
        return

    def get(self,key):
        """Gets an item out of the self.locals dict by key."""
        self._datalock.acquire()
        result = self.locals.get(key, NotDefined(key))
        self._datalock.release()
        return result
        
    def get_stdin(self):
        self._inouterr_lock.acquire()
        result = self._stdin
        self._inouterr_lock.release()
        return result
        
    def get_stdout(self):
        self._inouterr_lock.acquire()
        result = self._stdout
        self._inouterr_lock.release()
        return result
                
    def get_stderr(self):
        self._inouterr_lock.acquire()
        result = self._stderr
        self._inouterr_lock.release()
        return result
        
    def get_result(self,i):
        self._inouterr_lock.acquire()
        if i in range(len(self._stdin)):
            in_result = self._stdin[i]
            out_result = self._stdout[i]
            err_result = self._stderr[i]
        else:
            in_result = None
            out_result = None
            err_result = None
        self._inouterr_lock.release()
        
        if in_result:
            return (in_result, out_result, err_result)
        else:
            return None
            
    def get_last_result(self):
        self._inouterr_lock.acquire()
        in_result = self._stdin[-1]
        out_result = self._stdout[-1]
        err_result = self._stderr[-1]
        cmd_num = len(self._stdin) - 1
        self._inouterr_lock.release()
        return (cmd_num, in_result, out_result, err_result)
        
class QueuedInteractiveConsole:

    def __init__(self):
        self.workq = TicketedQueue()
        self.tic = TrappingInteractiveConsole()
     
    def start_work(self):
        t = threading.Thread(target=self._work)
        t.setDaemon(1)
        self.work_thread = t
        t.start()

    def _check_worker(self):
        if not self.work_thread.isAlive():
            self.start_work()

    def _work(self):
        while True:
            action = self.workq.get()
            #print "Action: ", action
            if action[0] == 'STOP':
                break
            f = getattr(self,'_handle_%s' % action[0], None)
            if f:
                f(action[1])
                             
    def _handle_PUSH(self, (dict_of_data, notifier)):
        #print "Handling PUSH..."
        self.tic.update(dict_of_data)
        #print "Pushed:", dict_of_data

    def _handle_PULL(self, (key, notifier)):
        #print "Handling PULL..."             
        data = self.tic.get(key)
        notifier.put(data)
        #print "Pulled data:", key, data
                
    def _handle_EXECUTE(self, (source, notifier)):
        #print "Handling EXECUTE..."
        self.tic.runsource(source)
        if notifier:
            notifier.put(self.tic.get_last_result())
                               
    def get_ticket(self):
        return self.workq.get_ticket()

    def stop_work(self):
        self.workq.put(('STOP',))
                     
    def push(self, key, value, ticket=None):
        """Push a python object into the kernel's namespace.
        
        This method should put the data on the queue and return immediately.
        
        Errors that occur in putting the data on the queue should be raised,
        but this method should not wait around for the data to be added to
        the namespace.  
        
        What about errors that occur when the data is added to the namespace?
        """
        notifier = None
        self.workq.put(('PUSH',({key:value}, notifier)), ticket)
        
    def pull(self, key, ticket=None):
        """Pull a python object off the kernel's namespace.
        
        This method should block until the data is actually ready to be 
        returned.  This will require that the work queue has been emptied.
        This means that it could be a while before this happends.
        
        What should be returned if the key doesn't exist?  Probably None
        """
        notifier = Queue.Queue(1)
        self.workq.put(('PULL', (key, notifier)), ticket)
        result = notifier.get(block=True)        
        return result
        
    def execute(self, source, ticket=None, block=True):
        """Execute python source code in the kernel's namespace.
        
        This method should have an option to block or not block.
        """
        if block:
            notifier = Queue.Queue(1)
            self.workq.put(('EXECUTE', (source, notifier)), ticket)
            result = notifier.get(block=True)
            return result
        else:
            notifier = None
            self.workq.put(('EXECUTE', (source, notifier)), ticket)
            return
        
    def status(self):
        return self.workq.qsize()
        
    def reset(self):
        # Currently this won't reset things until the queue is empty!
        self.stop_work()
        del self.tic
        self.tic = TrappingInteractiveConsole()
        self.start_work()
                    
    def get_stdin(self):
        return self.tic.get_stdin()
        
    def get_stdout(self):
        return self.tic.get_stdout()
                
    def get_stderr(self):
        return self.tic.get_stderr()
        
    def get_result(self,i):
        return self.tic.get_result(i)
        
    def get_last_result(self):
        return self.tic.get_last_result()

