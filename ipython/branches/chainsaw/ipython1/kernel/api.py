#!/usr/bin/env python
# encoding: utf-8
"""
api.py

Created by Brian Granger on 2006-08-25.
Copyright (c) 2006 __MyCompanyName__. All rights reserved.
"""
from ipython1.config.objects import ClientConfiguration
from ipython1.config.loader import configure

clientConfig = ClientConfiguration()
configure(clientConfig)

import ipython1.kernel.magic

RemoteController = clientConfig.RemoteController
RemoteController.MAX_LENGTH = clientConfig.maxMessageSize
defaultController = clientConfig.connectToControllerOn

del configure
del ClientConfiguration
