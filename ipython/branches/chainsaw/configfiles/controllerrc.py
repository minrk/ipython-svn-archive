#!/usr/bin/env python
# encoding: utf-8
"""
controllerrc.py
"""

# Get a valid configuration object for the controller

from ipython1.config.api import getConfigObject 

controllerrc = getConfigObject('controller')

# Now we can configure the controller

from ipython1.kernel.enginevanilla import \
    IVanillaEngineServerFactory

from ipython1.kernel.controllervanilla import \
    IVanillaControllerFactory

from ipython1.kernel.controllerpb import \
    IPBControllerFactory

# Set the network protocol used to talk to engines
controllerrc.engineServerProtocolInterface = IVanillaEngineServerFactory

# Set the interface and port to listen for engines on
controllerrc.listenForEnginesOn  = ('', 10201)

# Set the client interfaces to start
# Just the vanilla protocol
controllerrc.clientInterfaces = [(IVanillaControllerFactory, ('', 10105))]
# The vanilla protocol and PB
#controllerrc.clientInterfaces = [(IVanillaControllerFactory, ('', 10105)),
#                                  (IPBControllerFactory, ('', 10111))]

# Set the maximum message size
controllerrc.maxMessageSize = 99999999

