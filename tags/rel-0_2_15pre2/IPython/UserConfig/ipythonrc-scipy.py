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
# directory as .ipythonrc-scipy, it can be loaded by calling
#  ipython -profile scipy
# or just
#  ipython -p scipy

# A simple alias scipy -> ipython -p scipy makes life very convenient.

# This example is meant to load several modules to turn ipython into a very
# capable environment for high-end numerical work, similar to IDL or MatLab
# but with the beauty of the Python language.

# load our basic configuration with generic options
include ipythonrc

# import ...
import_mod 

# from ... import ...
import_some  

# Now we load all of SciPy
# from ... import *
import_all scipy IPython.numutils

# code 
execute print 'Welcome to the SciPy Scientific Computing Environment.'

# File with alternate printer system for Numeric Arrays.
# Files in the 'Extensions' directory will be found by IPython automatically
# (otherwise give the explicit path):
execfile Extensions/numeric_formats.py
