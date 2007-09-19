from ipython1.external.configobj import ConfigObj
from ipython1.config.api import ConfigObjManager

defaultCoreConfig = ConfigObj()
defaultCoreConfig['shell'] = {
    'shellClass': 'ipython1.core.interpreter.Interpreter',
    'shellImportStatement': ''
    }

configManager = ConfigObjManager(defaultCoreConfig, 'ipython1.core.ini')