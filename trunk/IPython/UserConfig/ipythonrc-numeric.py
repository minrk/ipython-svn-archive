# -*- Mode: Shell-Script -*-  Not really, but shows comments correctly
#***************************************************************************
#
# Configuration file for ipython -- ipythonrc format
#
# The format of this file is one of 'key value' lines.
# Lines containing only whitespace at the beginning and then a # are ignored
# as comments. But comments can NOT be put on lines with data.
#***************************************************************************

# This is an example of a 'profile' file which includes a base file and adds
# some customizaton for a particular purpose.

# If this file is found in the executing directory or in the user's home
# directory as .ipythonrc-numeric, it can be loaded by calling
#  ipython -profile numeric
# or just
#  ipython -p numeric

# A simple alias numpy -> 'ipython -p numeric' makes life very convenient.

# This example is meant to load several modules to turn IPython into a very
# capable environment for high-end numerical work, similar to IDL or MatLab
# but with the beauty and flexibility of the Python language.

# Load the user's basic configuration
include ipythonrc

# import ...

# Load Numeric by itself so that 'help Numeric' works
import_mod Numeric

# from ... import *
# GnuplotRuntime loads Gnuplot and adds enhancements for use in IPython
import_all Numeric IPython.numutils IPython.GnuplotInteractive

# a simple line at zero, often useful for an x-axis
execute xaxis=gpfunc('0',title='',with='lines lt -1')

# Below are optional things off by default. Uncomment them if desired.

# MA (MaskedArray) modifies the Numeric printing mechanism so that huge arrays
# are only summarized and not printed (which may freeze the machine for a
# _long_ time).

#import_mod MA


# gracePlot is a Python interface to the plotting package Grace.
# For more details go to: http://www.idyll.org/~n8gray/code/index.html
# Uncomment lines below if you have grace and its python support code

#import_mod gracePlot 
#execute grace = gracePlot.gracePlot  # alias to make gracePlot instances
#execute print '*** grace is an alias for gracePlot.gracePlot'

# Files to execute
execfile
