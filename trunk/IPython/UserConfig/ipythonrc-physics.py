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
# directory as .ipythonrc-physics, it can be loaded by calling
#  ipython -profile physics
# or just
#  ipython -p physics

# This profile loads modules useful for doing interactive calculations with
# physical quantities (with units). It relies on modules from Konrad Hinsen's
# ScientificPython (http://starship.python.net/crew/hinsen/)

# First load basic user configuration
include ipythonrc

# import ...
# Module with alternate input syntax for PhysicalQuantity objects.
import_mod IPython.Extensions.PhysicalQInput

# from ... import *
# math CANNOT be imported after PhysicalQInteractive. It will override the
# functions defined there.
import_all math IPython.Extensions.PhysicalQInteractive

# from ... import ...
import_some  

# code
execute q = PhysicalQuantityInteractive
execute g = PhysicalQuantityInteractive('9.8 m/s**2')
ececute rad = pi/180.
execute print '*** q is an alias for PhysicalQuantityInteractive'
execute print '*** g = 9.8 m/s^2 has been defined'
execute print '*** rad = pi/180  has been defined'

# Files to execute
execfile 
