#!/usr/bin/env python
# encoding: utf-8   -> do we need these now?
"""
Magic command interface for interactive parallel work.

Created by Brian Granger on 2006-08-17.
Copyright (c) 2006 __MyCompanyName__. All rights reserved.
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
#from ipython1.kernel import controllerclient

def magic_px(self,parameter_s=''):
    """Executes the given python command on the active IPython cluster.
    
    To activate a cluster in IPython, first create it and then call
    the activate() method.
    
    Then you can do the following:
     
    >>> %px a = 5       # Runs a = 5 on all nodes
    """
    #print 'Magic function. Passed parameter is between < >: <'+parameter_s+'>'
    #print 'The self object is:',self
    active_cluster = __IPYTHON__.active_cluster
    if active_cluster:
        print "Executing command on cluster"
        #if isinstance(active_cluster, cc.SubCluster):
        #    active_cluster.execute(parameter_s)
        #else:
        #    active_cluster.executeAll(parameter_s)
        active_cluster.executeAll(parameter_s)
    else:
        print "Error: No active IPython cluster.  Use activate()."
        
def magic_pn(self,parameter_s=''):
    """Executes the given python command on the active IPython cluster.
    
    To activate a cluster in IPython, first create it and then call
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
            
    active_cluster = __IPYTHON__.active_cluster
    if active_cluster:
        print "Executing command on cluster"
        active_cluster.execute(k, cmd)
    else:
        print "Error: No active IPython cluster.  Use activate()."

    
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
        #if isinstance(active_cluster, cc.SubCluster):
        #    self.active_cluster.execute(source)
        #else:
        #    self.active_cluster.executeAll(source)
        self.active_cluster.executeAll(source)
        return False
    
def magic_autopx(self, parameter_s=''):

    # Build and activate a subcluster if needed 
    if parameter_s:
        exec_str = 'kernels = %s' % parameter_s
        try:
            exec exec_str
        except:
            print "Argument of autopx must evaluate to a list"
            return
        else:
            print "Autoparallel mode will use kernels: ", kernels
            self.saved_active_cluster = self.active_cluster
            ic = self.active_cluster.subcluster(kernels)
            self.active_cluster = ic            
    
    if hasattr(self, 'autopx'):
        if self.autopx == True:
            self.runsource = new.instancemethod(InteractiveShell.runsource,
                self, self.__class__)
            self.autopx = False
            try:
                self.active_cluster = self.saved_active_cluster
            except:
                pass
            print "Auto Parallel Disabled" 
        else:
            self.runsource = new.instancemethod(pxrunsource, self,
                self.__class__)
            self.autopx = True
            print "Auto Parallel Enabled"
    else:
        self.runsource = new.instancemethod(pxrunsource, self,
                self.__class__)
        self.autopx = True
        print "Auto Parallel Enabled"

            
# Add the new magic function to the class dict:

InteractiveShell.magic_px = magic_px
InteractiveShell.magic_pn = magic_pn
InteractiveShell.magic_autopx = magic_autopx

# And remove the global name to keep global namespace clean.  Don't worry, the
# copy bound to IPython stays, we're just removing the global name.
del magic_px
del magic_autopx
del magic_pn

