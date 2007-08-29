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

from setuptools import setup, find_packages

setup(
    name = "ipython1",
    version = "0.9alpha2",
    packages = find_packages(),
    
    zip_safe = False,
    include_package_data = True,
    entry_points = {
            'console_scripts': ['ipengine = ipython1.scripts.ipengine:start',
                                'ipcontroller = ipython1.scripts.ipcontroller:start',
                                'ipnotebook = ipython1.scripts.ipnotebook:start',
                                'ipcluster = ipython1.scripts.ipcluster:main']
        },

    author = "Fernando Perez / Brian Granger",
    author_email = "Fernando.Perez@colorado.edu / ellisonbg@gmail.com",
    url = 'http://ipython.scipy.org',
    description = "Newly Redesigned IPython",
    license = "BSD",
    keywords = "ipython parallel distributed",
)