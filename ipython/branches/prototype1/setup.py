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

# This is needed to monkey patch sysconfig.customize_compiler for
# Python 2.3 so that the default LDSHARED can be overridden by the
# environmental variable below.
import ipython1.distutils.sysconfig


from distutils import sysconfig
from distutils.core import setup, Extension

# Set the paths for the mpi compiler binaries
mpi_base = ''
mpicc = mpi_base + 'mpicc'
mpicxx = mpi_base + 'mpic++'

# Swap out just the binary of the linker, but keep the flags
ldshared = sysconfig.get_config_var('LDSHARED')
ldshared = mpicc + ' ' + ldshared.split(' ',1)[1]

# Override the default compiler with the mpi one
os.environ['CC'] = mpicc
os.environ['CXX'] = mpicxx
os.environ['LDSHARED'] = ldshared

# Now build IPython

e = Extension('ipython1.mpi',['ipython1/mpi/mpi.c'])

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
                          'scripts/ipresults','scripts/ipcontroller',
                          'scripts/ipkernel-mpi'],
      ext_modules=[e]
      )
