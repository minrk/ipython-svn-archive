"""Init file"""
#*****************************************************************************
#       Copyright (C) 2005 Tzanko Matev. <tsanko@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

# Enforce proper version requirements
import sys
if sys.version[0:3] < '2.4':
    raise ImportError, 'Python Version 2.4 or above is required.'
        
# Define what gets imported with a 'from nbshell import *'
__all__ = ['Main', 'Release']

glob,loc = globals(),locals()
for name in __all__:
    __import__(name,glob,loc,[])

# Release data
from nbshell import Release # do it explicitly so pydoc can see it - pydoc bug
__author__  = '%s <%s>' % Release.author
__license__ = Release.license
__version__ = Release.version

#import the start function
from nbshell.Main import start

del sys,glob,loc