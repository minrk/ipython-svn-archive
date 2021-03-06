# -*- Mode: Shell-Script -*-  Not really, but shows comments correctly
#***************************************************************************
#
# Configuration file for ipython -- ipythonrc format
#
# The format of this file is one of 'key value' lines.
# Lines containing only whitespace at the beginning and then a # are ignored
# as comments. But comments can NOT be put on lines with data.
#***************************************************************************

# If this file is found in the executing directory or in the user's home
# directory as .ipythonrc-tutorial, it can be loaded by calling
#  ipython -profile tutorial
# or just
#  ipython -p tutorial

# This profile loads a special input line filter to allow typing lines which
# begin with '>>> ' or '... '. These two strings, if present at the start of
# the input line, are stripped. This allows for direct pasting of code from
# examples such as those available in the standard Python tutorial.

# First load basic user configuration
include ipythonrc

# import ...
# Module with alternate input syntax for PhysicalQuantity objects.
import_mod IPython.Extensions.InterpreterPasteInput

# from ... import *
import_all

# from ... import ...
import_some  

# code
execute

# Files to execute
execfile
