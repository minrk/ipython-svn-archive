# encoding: utf-8
"""
Sample configuration file for ipcontroller.
"""

# Get a valid configuration object for the controller

from ipython1.config.api import getConfigObject 

controllerConfig = getConfigObject('controller')

# Now we can configure the controller

controllerConfig.listenForEnginesOn['ip'] = '127.0.0.1'
controllerConfig.listenForEnginesOn['port'] = 20000