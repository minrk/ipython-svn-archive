#****************************************************************************
#       Copyright (C) 2005 Brian Granger. <bgranger@scu.edu>
#
#  Distributed under the terms of the BSD License.  
#****************************************************************************

"""Example of how to define a magic function for extending IPython.

The name of the function *must* begin with magic_. IPython mangles it so
that magic_foo() becomes available as %foo.

The argument list must be *exactly* (self,parameter_s='').

The single string parameter_s will have the user's input. It is the magic
function's responsability to parse this string.

That is, if the user types
>>>%foo a b c

The followinng internal call is generated:
   self.magic_foo(parameter_s='a b c').

To have any functions defined here available as magic functions in your
IPython environment, import this file in your configuration file with an
execfile = this_file.py statement. See the details at the end of the sample
ipythonrc file.  """

import new

from IPython.iplib import InteractiveShell

# fisrt define a function with the proper form:
def magic_px(self,parameter_s=''):
    """Executes the given python command on the active IPython cluster.
    
    To activate a cluster in IPython, first create it and then call
    the activate() method.
    
    Then you can do the following:
     
    %px a = 5       # Runs a = 5 on all nodes
    """
    #print 'Magic function. Passed parameter is between < >: <'+parameter_s+'>'
    #print 'The self object is:',self
    active_cluster = __IPYTHON__.active_cluster
    if active_cluster:
        print "Executing command on cluster"
        active_cluster.execute(parameter_s)
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
    if 'ipmagic("%autopx' in source:
        if self.runcode(code) == 0:
            return False
        else:
            return None
    else:
        self.active_cluster.execute(source)
        return False
    
def magic_autopx(self, parameter_s=''):

    if hasattr(self, 'autopx'):
        if self.autopx == True:
            self.runsource = new.instancemethod(InteractiveShell.runsource,
                self, self.__class__)
            self.autopx = False
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
InteractiveShell.magic_autopx = magic_autopx

# And remove the global name to keep global namespace clean.  Don't worry, the
# copy bound to IPython stays, we're just removing the global name.
del magic_px
del magic_autopx

#********************** End of file <example-magic.py> ***********************
