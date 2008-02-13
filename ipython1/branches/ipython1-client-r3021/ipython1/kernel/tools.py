# encoding: utf-8
"""
This module contains tools for doing interactive parallel work.

The functions and classes here are designed to be imported and used on Engines
that have a rank and size defined.  The functions here use these to determine
how to partition lists and arrays amongst the Engines.
"""
__docformat__ = "restructuredtext en"
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelley <benjaminrk@gmail.com>
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



