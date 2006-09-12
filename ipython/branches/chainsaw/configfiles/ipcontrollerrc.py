#!/usr/bin/env python
# encoding: utf-8
"""
ipcontrollerrc.py
"""

# Get a valid configuration object for the controller

from ipython1.config.api import getConfigObject 

controllerrc = getConfigObject('controller')

# Now we can configure the controller
