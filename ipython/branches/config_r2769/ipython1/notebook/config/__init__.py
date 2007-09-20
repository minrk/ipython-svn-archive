from ipython1.external.configobj import ConfigObj
from ipython1.config.cutils import getIpythonDir
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
    'activeDB': "sqlite:///%s/ipnotebooks.db"%(getIpythonDir()),
    'externalDBs': []
}

defaultNotebookConfig['notebook'] = notebookConfig

configManager = ConfigObjManager(defaultNotebookConfig, 'ipython1.notebook.ini')