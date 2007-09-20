# encoding: utf-8
__docformat__ = "restructuredtext en"
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelley <benjaminrk@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

from ipython1.external.configobj import ConfigObj
from ipython1.config.api import ConfigObjManager

defaultCoreConfig = ConfigObj()
defaultCoreConfig['shell'] = {
    'shellClass': 'ipython1.core.interpreter.Interpreter',
    'shellImportStatement': ''
    }

configManager = ConfigObjManager(defaultCoreConfig, 'ipython1.core.ini')