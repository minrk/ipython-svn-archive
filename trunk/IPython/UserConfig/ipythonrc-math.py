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
# directory as .ipythonrc-math, it can be loaded by calling
#  ipython -profile math
# or just
#  ipython -p math

# This example is a light customization to have ipython have basic math functions
# readily available, effectively making the python prompt a very capable scientific
# calculator

# include base config and only add some extras
include ipythonrc

# load the complex math functions but keep them in a separate namespace
import_mod cmath

# from ... import *
# load the real math functions in the global namespace for convenience
import_all math

# from ... import ...
import_some

# code to execute
execute print "*** math functions available globally, cmath as a module"