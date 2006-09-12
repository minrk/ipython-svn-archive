#!/usr/bin/env python
# encoding: utf-8
"""
controllerrc.py


"""

from ipython1.kernel.enginevanilla import \
    IVanillaEngineServerFactory

from ipython1.kernel.controllervanilla import \
    IVanillaControllerFactory

from ipython1.kernel.controllerpb import \
    IPBControllerFactory


# Set the network protocol used to talk to engines
#ControllerConfig.engineServerProtocolInterface = IVanillaEngineServerFactory

# Set the interface and port to listen for engines on
#ControllerConfig.listenForEnginesOn  = ('', 10201)

# Set the client interfaces to start
# Just the vanilla protocol
#ControllerConfig.clientInterfaces = [(IVanillaControllerFactory, ('', 10105))]
# The vanilla protocol and PB
#ControllerConfig.clientInterfaces = [(IVanillaControllerFactory, ('', 10105)),
#                                     (IPBControllerFactory, ('', 10111))]

#ControllerConfig.maxMessageSize = 99999999

