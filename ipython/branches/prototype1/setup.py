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

from distutils.core import setup, Extension
from distutils import sysconfig

def customize_compiler(compiler):
    """Do any platform-specific customization of a CCompiler instance.

    Mainly needed on Unix, so we can plug in the information that
    varies across Unices and is stored in Python's Makefile.
    """
    if compiler.compiler_type == "unix":
        (cc, cxx, opt, basecflags, ccshared, ldshared, so_ext) = \
            get_config_vars('CC', 'CXX', 'OPT', 'BASECFLAGS', 'CCSHARED', 'LDSHARED', 'SO')

        if os.environ.has_key('CC'):
            cc = os.environ['CC']
        if os.environ.has_key('CXX'):
            cxx = os.environ['CXX']
        if os.environ.has_key('LDSHARED'):
            ldshared = os.environ['LDSHARED']
        if os.environ.has_key('CPP'):
            cpp = os.environ['CPP']
        else:
            cpp = cc + " -E"           # not always
        if os.environ.has_key('LDFLAGS'):
            ldshared = ldshared + ' ' + os.environ['LDFLAGS']
        if basecflags:
            opt = basecflags + ' ' + opt
        if os.environ.has_key('CFLAGS'):
            opt = opt + ' ' + os.environ['CFLAGS']
            ldshared = ldshared + ' ' + os.environ['CFLAGS']
        if os.environ.has_key('CPPFLAGS'):
            cpp = cpp + ' ' + os.environ['CPPFLAGS']
            opt = opt + ' ' + os.environ['CPPFLAGS']
            ldshared = ldshared + ' ' + os.environ['CPPFLAGS']

        cc_cmd = cc + ' ' + opt
        compiler.set_executables(
            preprocessor=cpp,
            compiler=cc_cmd,
            compiler_so=cc_cmd + ' ' + ccshared,
            compiler_cxx=cxx,
            linker_so=ldshared,
            linker_exe=cc)

        compiler.shared_lib_extension = so_ext

__customize_compiler = sysconfig.customize_compiler

sysconfig.customize_compiler = customize_compiler

# Configure distutils to use mpicc/mpicxx for building    
mpi_base = ''
mpicc = mpi_base + 'mpicc'
mpicxx = mpi_base + 'mpic++'

# Swap out just the binary of the linker, but keep the flags
ldshared = sysconfig.get_config_var('LDSHARED')
ldshared = mpicc + ' ' + ldshared.split(' ',1)[1]

os.environ['CC'] = mpicc
os.environ['CXX'] = mpicxx
os.environ['LDSHARED'] = ldshared

e = Extension('ipython1.mpi',['ipython1/mpi/mpi.c'])

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
                          'scripts/ipresults','scripts/ipcontroller',
                          'scripts/ipkernel-mpi'],
      ext_modules=[e]
      )
