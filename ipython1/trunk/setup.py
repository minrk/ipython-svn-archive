#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup script for ipython's kernel package.
"""

#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelley <benjaminrk@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

import sys
from setuptools import setup, find_packages

#---------------------------------------------------------------------------
# Test for dependencies
#---------------------------------------------------------------------------

from setupext import print_line, print_raw, print_status, print_message, \
    check_for_ipython, check_for_zopeinterface, check_for_twisted, \
    check_for_pexpect, check_for_httplib2, check_for_sqlalchemy, \
    check_for_simplejson

print_line()
print_raw("BUILDING IPYTHON1")
print_status('python', sys.version)
print_status('platform', sys.platform)
if sys.platform == 'win32':
    print_status('Windows version', sys.getwindowsversion())
print_raw("")
print_raw("REQUIRED DEPENDENCIES")

if not check_for_ipython():
    sys.exit(1)
if not check_for_zopeinterface():
    sys.exit(1)
if not check_for_twisted():
    sys.exit(1)

print_raw("")
print_raw("OPTIONAL DEPENDENCIES")

check_for_pexpect()
check_for_httplib2()
check_for_sqlalchemy()
check_for_simplejson()

#---------------------------------------------------------------------------
# The actual setup
#---------------------------------------------------------------------------


setup(
    name = "ipython1",
    version = "0.9alpha3",
    packages = find_packages(),
    
    zip_safe = False,
    include_package_data = True,
    entry_points = {
            'console_scripts': ['ipengine = ipython1.kernel.scripts.ipengine:start',
                                'ipcontroller = ipython1.kernel.scripts.ipcontroller:start',
                                'ipnotebook = ipython1.notebook.scripts.ipnotebook:start',
                                'ipcluster = ipython1.kernel.scripts.ipcluster:main']
        },

    author = "Fernando Perez / Brian Granger",
    author_email = "Fernando.Perez@colorado.edu / ellisonbg@gmail.com",
    url = 'http://ipython.scipy.org',
    description = "Newly Redesigned IPython",
    license = "BSD",
    keywords = "ipython parallel distributed",
)