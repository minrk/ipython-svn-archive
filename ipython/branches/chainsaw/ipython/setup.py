#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup script for ipython's kernel package.
"""

#*****************************************************************************
#       Copyright (C) 2001-2005 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from distutils.core import setup

# Call the setup() routine which does most of the work
setup(name             = 'ipkernel',
      version          = '0.1',
      description      = 'ipython kernel - temporary package',
      long_description = 'ipython kernel - temporary package',
      author           = 'Brian / Fernando',
      author_email     = 'Brian / Fernando',
      url              = 'http://ipython.scipy.org',
      license          = 'BSD',
      packages         = ['kernel'],
      scripts          = ['scripts/startkernel','scripts/startkernelwx'],

      )
