#!/usr/bin/env python
# encoding: utf-8
"""
clientrc.py

"""

# Get a valid configuration object for the client

from ipython1.config.api import getConfigObject 

clientrc = getConfigObject('client')

# Now we can configure the client

from ipython1.kernel.controllervanilla import RemoteController

clientrc.RemoteController = RemoteController
clientrc.connectToControllerOn = ('127.0.0.1', 10105)
clientrc.maxMessageSize = 99999999