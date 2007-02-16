# encoding: utf-8
"""
Sample configuration file for ipengine.
"""

# Get a valid configuration object for the engine and shell

from ipython1.config.api import getConfigObject 

engineConfig = getConfigObject('engine')
shellConfig = getConfigObject('shell')

# Now we can configure the engine and shell

engineConfig.connectToControllerOn['ip'] = '127.0.0.1'
engineConfig.connectToControllerOn['port'] = 20000

