#!/usr/bin/env python
# encoding: utf-8   -> do we need these now?
"""
Magic command interface for interactive parallel work.
"""
#*****************************************************************************
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import new

from IPython.iplib import InteractiveShell

NO_ACTIVE_CONTROLLER = """
Error:  No Controller is activated
Use activate() on a RemoteController object to activate it more magics.
"""

def magic_px(self,parameter_s=''):
    """Executes the given python command on the active IPython Controller.
    
    To activate a Controller in IPython, first create it and then call
    the activate() method.
    
    Then you can do the following:
     
    >>> %px a = 5       # Runs a = 5 on all nodes
    """
    #print 'Magic function. Passed parameter is between < >: <'+parameter_s+'>'
    #print 'The self object is:',self
    try:
        activeController = __IPYTHON__.activeController
    except AttributeError:
        print NO_ACTIVE_CONTROLLER
    else:
        print "Executing command on Controller"
        activeController.executeAll(parameter_s)

def magic_pn(self,parameter_s=''):
    """Executes the given python command on the active IPython cluster.
    
    To activate a Controller in IPython, first create it and then call
    the activate() method.
    
    Then you can do the following:
     
    >>> %pn 0 a = 5       # Runs a = 5 on kernel 0
    """
    args = parameter_s.split(" ", 1)
    if len(args) == 2:
        try:
            k = int(args[0])
        except:
            print "Usage: %pn kernel command"
            return
    else:
            print "Usage: %pn kernel command"
            return
    cmd = args[1]
    
    try:
        activeController = __IPYTHON__.activeController
    except AttributeError:
        print NO_ACTIVE_CONTROLLER
    else:
        print "Executing command on cluster"
        activeController.execute(k, cmd)

def pxrunsource(self, source, filename="<input>", symbol="single"):

    try:
        code = self.compile(source, filename, symbol)
    except (OverflowError, SyntaxError, ValueError):
        # Case 1
        self.showsyntaxerror(filename)
        return None

    if code is None:
        # Case 2
        return True

    # Case 3
    # We store the code object so that threaded shells and
    # custom exception handlers can access all this info if needed.
    # The source corresponding to this can be obtained from the
    # buffer attribute as '\n'.join(self.buffer).
    self.code_to_run = code
    # now actually execute the code object
    if '_ip.magic("%autopx' in source:
        if self.runcode(code) == 0:
            return False
        else:
            return None
    else:
        #if isinstance(activeController, cc.SubCluster):
        #    self.activeController.execute(source)
        #else:
        #    self.activeController.executeAll(source)
        self.activeController.executeAll(source)
        return False
    
def magic_autopx(self, parameter_s=''):
    
    if hasattr(self, 'autopx'):
        if self.autopx == True:
            self.runsource = new.instancemethod(InteractiveShell.runsource,
                self, self.__class__)
            self.autopx = False
            print "Auto Parallel Disabled" 
        else:
            try:
                activeController = __IPYTHON__.activeController
            except AttributeError:
                print NO_ACTIVE_CONTROLLER
            else:
                self.runsource = new.instancemethod(pxrunsource, self, self.__class__)
                self.autopx = True
                print "Auto Parallel Enabled\nType %autopx to disable"
    else:
        try:
            activeController = __IPYTHON__.activeController
        except AttributeError:
            print NO_ACTIVE_CONTROLLER
        else:
            self.runsource = new.instancemethod(pxrunsource, self, self.__class__)
            self.autopx = True
            print "Auto Parallel Enabled\nType %autopx to disable"

            
# Add the new magic function to the class dict:

InteractiveShell.magic_px = magic_px
InteractiveShell.magic_pn = magic_pn
InteractiveShell.magic_autopx = magic_autopx

# And remove the global name to keep global namespace clean.  Don't worry, the
# copy bound to IPython stays, we're just removing the global name.
del magic_px
del magic_autopx
del magic_pn

