#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup script for ipython's kernel package.
"""

#*****************************************************************************
#       Copyright (C) 2001-2005 Fernando Perez <fperez@colorado.edu>
#                     2005-2006 Brian Granger <ellisonbg@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import os
# BEFORE importing distutils, remove MANIFEST. distutils doesn't properly
# update it when the contents of directories change.
if os.path.exists('MANIFEST'): os.remove('MANIFEST')

from distutils.core import setup

# Call the setup() routine which does most of the work
setup(name             = 'ipython1',
      version          = '0.1',
      description      = 'Newly Redesigned IPython',
      long_description = 'Newly Redesigned IPython',
      author           = 'Fernando Perez / Brian Granger',
      author_email     = 'Fernando.Perez@colorado.edu / ellisonbg@gmail.com',
      url              = 'http://ipython.scipy.org',
      license          = 'BSD',
      packages         = ['ipython1','ipython1.kernel','ipython1.core',
                          'ipython1.startup'],
      scripts          = ['scripts/ipkernel','scripts/ipkernelwx',
                          'scripts/ipresults'],
      )
