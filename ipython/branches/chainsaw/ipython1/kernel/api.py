#!/usr/bin/env python
# encoding: utf-8
"""This module contains the public API for working with a remote controller.

It looks at the client configuration to see what network protocol should be
used and then loads the appropriate client.
"""
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

import ipython1.config.api as config
clientConfig = config.getConfigObject('client')

import ipython1.kernel.maÅgic

RemoteController = clientConfig.RemoteController
RemoteController.MAX_LENGTH = clientConfig.maxMessageSize
defaultController = clientConfig.connectToControllerOn