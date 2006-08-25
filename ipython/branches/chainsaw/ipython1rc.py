#!/usr/bin/env python
# encoding: utf-8
"""
Configuration file for ipython1.
"""

from ipython1.kernel.enginevanilla import \
    IVanillaEngineClientFactory, IVanillaEngineServerFactory

from ipython1.kernel.controllervanilla import \
    IVanillaControllerFactory

enginePort = 10201
    
engineClientProtocolInterface = IVanillaEngineClientFactory

engineServerProtocolInterface = IVanillaEngineServerFactory

clientInterfaces = []

clientInterfaces.append((IVanillaControllerFactory, 10105))

maxMessageSize = 999999

mpiImportStatement = 'import ipython1.mpi as mpi'
