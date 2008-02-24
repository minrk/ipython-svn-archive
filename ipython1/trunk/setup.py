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

import os, sys
from configobj import ConfigObj

# BEFORE importing disutils, remove MANIFEST. distutils doesn't properly
# update it when the contents of directories change.
if os.path.exists('MANIFEST'): os.remove('MANIFEST')

from distutils.core import setup

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
# Get things ready for setup
#---------------------------------------------------------------------------

# The values in setup.cfg override these
notebook = True
kernel = True
frontend = True

if os.path.exists('setup.cfg'):
    install_config = ConfigObj('setup.cfg')
else:
    install_config = None

if install_config is not None:
    notebook = bool(install_config['packages']['notebook'])
    kernel = bool(install_config['packages']['kernel'])
    frontend = bool(install_config['packages']['frontend'])

def add_package(packages, pname, config=False, tests=False, scripts=False, others=None):
    packages.append('.'.join(['ipython1',pname]))
    if config:
        packages.append('.'.join(['ipython1',pname,'config']))
    if tests:
        packages.append('.'.join(['ipython1',pname,'tests']))
    if scripts:
        packages.append('.'.join(['ipython1',pname,'scripts']))
    if others is not None:
        for o in others:
            packages.append('.'.join(['ipython1',pname,o]))
       
def add_external(packages):
    packages.append('ipython1.external')
    packages.append('ipython1.external.MochiKit')
    packages.append('ipython1.external.twisted')
    packages.append('ipython1.external.twisted.web2')
    packages.append('ipython1.external.twisted.web2.auth')
    packages.append('ipython1.external.twisted.web2.channel')
    packages.append('ipython1.external.twisted.web2.client')
    packages.append('ipython1.external.twisted.web2.dav')
    packages.append('ipython1.external.twisted.web2.dav.element')
    packages.append('ipython1.external.twisted.web2.dav.method')
    packages.append('ipython1.external.twisted.web2.filter')
           
packages = ['ipython1']
add_package(packages, 'config')
add_package(packages, 'core', config=True, tests=True)
add_external(packages)
add_package(packages, 'tests')
add_package(packages, 'testutils', tests=True)
add_package(packages, 'tools', tests=True)

if notebook:
    add_package(packages, 'notebook', config=True, tests=True, scripts=True)
if kernel:
    add_package(packages, 'kernel', config=True, tests=True, scripts=True)
if frontend:
    add_package(packages, 'frontend', others=['snippets'])

# Currently, sdist doesn't pick this stuff up.  How to handle it?
package_data = {'ipython1': ['external/MochiKit/*.js'],
    '': ['*.txt']}

scripts = []

if kernel:
    scripts.append('ipython1/kernel/scripts/ipengine')
    scripts.append('ipython1/kernel/scripts/ipcontroller')
    scripts.append('ipython1/kernel/scripts/ipcluster')
if notebook:
    scripts.append('ipython1/notebook/scripts/ipnotebook')

#---------------------------------------------------------------------------
# The actual setup
#---------------------------------------------------------------------------


setup(
    name = "ipython1",
    version = "0.3alpha1",
    packages = packages,
    package_data = package_data,
    scripts = scripts,
    author = "Fernando Perez / Brian Granger",
    author_email = "Fernando.Perez@colorado.edu / ellisonbg@gmail.com",
    url = 'http://ipython.scipy.org',
    description = "Newly Redesigned IPython",
    license = "BSD",
    keywords = "ipython parallel distributed",
)