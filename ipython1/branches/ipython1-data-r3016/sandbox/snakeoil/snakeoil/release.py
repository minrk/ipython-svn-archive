# -*- coding: utf-8 -*-
"""Release data for SnakeOil.

$Id: Release.py 1113 2006-01-31 03:45:10Z fperez $"""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#       Copyright (C) 2007  Fernando Perez <Fernando.Perez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelley <benjaminrk@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------


# Name of the package for release purposes.  This is the name which labels
# the tarballs and RPMs made by distutils, so it's best to lowercase it.

name = 'snakeoil'

# For versions with substrings (like 0.6.16.svn), use an extra . to separate
# the new substring.  We have to avoid using either dashes or underscores,
# because bdist_rpm does not accept dashes (an RPM) convention, and
# bdist_deb does not accept underscores (a Debian convention).

version = '0.1.alpha'

revision = '$Revision: 1113 $'

description = "Improved testing workflows in Python with doctest and unittest."

long_description = \
"""
SnakeOil - Python testing that doesn't squeak.

This module provides a few small utilities for easier/smoother testing
workflows in Python, using only the facilities of the standard library (doctest
and unittest).  While it can be installed as a package via setup.py, it is
meant to be small enough that projects wanting to use it can just copy a few
files into their testing directory and use carry it internally, thus avoiding
the need to create an external dependency on SnakeOil.

Its main purposes are (see the docs for more details):

- Easy creation of parametric tests (unittests that take arguments).

- Immediate use of any standalone testing script as a unit test, without having
to subclass anything.

- Easy mechanisms for creating valid doctest (.txt) files from true Python
sources, so that one can edit real Python code in an editor and convert that
code to a set of doctests with minimal effort.
"""

license = 'BSD'

authors = {'Fernando' : ('Fernando Perez','Fernando.Perez@colorado.edu'),
           'Brian' : ('Brian Granger','ellisonbg@gmail.com'),
           'Min' : ('Fernando Perez','benjaminrk@gmail.com'),
           }

url = 'http://ipython.scipy.org'

download_url = 'http://ipython.scipy.org/dist'

platforms = ['Linux','Mac OSX']

keywords = ['testing','unittest','doctest','agile']
