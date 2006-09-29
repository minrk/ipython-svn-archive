#!/usr/bin/env python
# encoding: utf-8
"""
This module contains tools for doing interactive parallel work.

The functions and classes here are designed to be imported and used on Engines
that have a rank and size defined.  The functions here use these to determine
how to partition lists and arrays amongst the Engines.
"""
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import sys
import os

#-------------------------------------------------------------------------------
# Utilities
#-----------------------------------------------------------------------------

print globals()

global size, rank
print size, rank

def getSizeAndRank():

    try:
        size, rank
    except NameError:
        return None
    else:
        return size, rank

#-------------------------------------------------------------------------------
# Distributed versions of some standard Python datatypes.
#-------------------------------------------------------------------------------

def drange(start, stop, step):
    """A distributed range object."""
    
    sizerank = getSizeAndRank()
    if sizerank is None:
        print "Globals size and rank must be defined."
        return
    else:
        size, rank = sizerank
    
#-------------------------------------------------------------------------------
# Distributed versions of numpy arrays.
#-------------------------------------------------------------------------------
    
try:
    import numpy
except ImportError:
    pass
else:
    def darange(start, stop, step):
        """A distributed version of arange."""
        
        sizerank = getSizeAndRank()
        if sizerank is None:
            print "Globals size and rank must be defined."
            return
        else:
            size, rank = sizerank
        
    def dlinspace(start, stop, n):
        """A distributed version of linspace."""
        
        sizerank = getSizeAndRank()
        if sizerank is None:
            print "Globals size and rank must be defined."
            return
        else:
            size, rank = sizerank
    
