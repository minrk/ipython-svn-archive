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
from ipython1.config.cutils import get_ipython_dir
from ipython1.config.api import ConfigObjManager

defaultNotebookConfig = ConfigObj()
    
#-------------------------------------------------------------------------------
# Notebook Configuration
#-------------------------------------------------------------------------------

notebookConfig = {
    'engineInterface': 'ipython1.kernel.engineservice.IEngineQueued',
    'networkInterfaces': {
        'http': {
            'interface': 'ipython1.notebook.notebookhttp.IHTTPNotebookServerFactory',
            'ip'    : '',
            'port'  : 8008
        }
    },
    'defaultDBMode': "sqlite///",
    'activeDB': "sqlite://%s/ipnotebooks.db"%(get_ipython_dir()),
    'externalDBs': []
}

defaultNotebookConfig['notebook'] = notebookConfig

configManager = ConfigObjManager(defaultNotebookConfig, 'ipython1.notebook.ini')
