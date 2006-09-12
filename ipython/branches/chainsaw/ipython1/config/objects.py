#!/usr/bin/env python
# encoding: utf-8
"""
Configuration objects.
"""
#*****************************************************************************
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

# Imports

from ipython1.config.base import ConfigurationBase, ConfigData

# Global defaults
    
maxMesageSize = 99999999
enginePort = 10201
clientVanillaPort = 10105

# Engine configrations

from ipython1.kernel.enginevanilla import \
    IVanillaEngineClientFactory

from ipython1.core.shell import InteractiveShell

class EngineConfigData(ConfigData):
    connectToControllerOn = ('127.0.0.1', enginePort)
    engineClientProtocolInterface = IVanillaEngineClientFactory
    engineShell = InteractiveShell
    maxMessageSize = maxMesageSize
    mpiImportStatement = ''
    
class EngineConfig(ConfigurationBase):
    configDataClass = EngineConfigData
    configFiles = ['ipython1rc.py', 'enginerc.py']
    
# Controller configruation

from ipython1.kernel.enginevanilla import \
    IVanillaEngineServerFactory

from ipython1.kernel.controllervanilla import \
    IVanillaControllerFactory
    
class ControllerConfigData(ConfigData):
    engineServerProtocolInterface = IVanillaEngineServerFactory
    listenForEnginesOn  = ('', enginePort)
    clientInterfaces = [(IVanillaControllerFactory, ('', clientVanillaPort))]
    maxMessageSize = maxMesageSize
    
class ControllerConfig(ConfigurationBase):
    configDataClass = ControllerConfigData
    configFiles = ['ipython1rc.py', 'controllerrc.py']
    
# Client configuration

from ipython1.kernel.controllervanilla import \
    RemoteController

class ClientConfigData(ConfigData):    
    RemoteController = RemoteController
    connectToControllerOn = ('127.0.0.1', clientVanillaPort)
    maxMessageSize = maxMesageSize

class ClientConfig(ConfigurationBase):
    configDataClass = ClientConfigData
    configFiles = ['ipython1rc.py', 'clientrc.py']
   




