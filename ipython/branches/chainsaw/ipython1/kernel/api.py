#!/usr/bin/env python
# encoding: utf-8
"""
api.py

Created by Brian Granger on 2006-08-25.
Copyright (c) 2006 __MyCompanyName__. All rights reserved.
"""

import ipython1.config.api as config
clientConfig = config.getConfigObject('client')

import ipython1.kernel.magic

RemoteController = clientConfig.RemoteController
RemoteController.MAX_LENGTH = clientConfig.maxMessageSize
defaultController = clientConfig.connectToControllerOn