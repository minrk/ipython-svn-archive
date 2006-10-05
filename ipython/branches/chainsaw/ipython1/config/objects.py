#!/usr/bin/env python
# encoding: utf-8
"""
Configuration objects.
"""
__docformat__ = "restructuredtext en"
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

# Imports

from ipython1.config.base import ConfigHelper, Config

# Global defaults
    
maxMesageSize = 99999999
enginePort = 10201
clientVanillaPort = 10105

# Shell configuration

from ipython1.core.shell import InteractiveShell

class ShellConfig(Config):
    shellClass = InteractiveShell
    filesToRun = []
    
class ShellConfigHelper(ConfigHelper):
    configClass = ShellConfig

# Engine configrations

from ipython1.kernel.enginevanilla import \
    IVanillaEngineClientFactory

class EngineConfig(Config):
    connectToControllerOn = ('127.0.0.1', enginePort)
    engineClientProtocolInterface = IVanillaEngineClientFactory
    maxMessageSize = maxMesageSize
    mpiImportStatement = ''
    #mpiImportStatement = 'from mpi4py import MPI as mpi'
    
class EngineConfigHelper(ConfigHelper):
    configClass = EngineConfig
    
# Controller configuration

from ipython1.kernel.enginevanilla import \
    IVanillaEngineServerFactory

from ipython1.kernel.controllervanilla import \
    IVanillaControllerFactory
    
from ipython1.kernel.controllerpb import \
    IPBControllerFactory
    
class ControllerConfig(Config):
    engineServerProtocolInterface = IVanillaEngineServerFactory
    listenForEnginesOn  = ('', enginePort)
    clientInterfaces = [(IVanillaControllerFactory, ('', clientVanillaPort)),
                        (IPBControllerFactory, ('', 10111))]
    maxMessageSize = maxMesageSize
    
class ControllerConfigHelper(ConfigHelper):
    configClass = ControllerConfig
    
# Client configuration

from ipython1.kernel.controllervanilla import \
    RemoteController

class ClientConfig(Config):    
    RemoteController = RemoteController
    connectToControllerOn = ('127.0.0.1', clientVanillaPort)
    maxMessageSize = maxMesageSize

class ClientConfigHelper(ConfigHelper):
    configClass = ClientConfig

# All top-level config classes must be listed here.

configHelperClasses = {'engine'     : EngineConfigHelper,
                       'controller' : ControllerConfigHelper,
                       'client'     : ClientConfigHelper,
                       'shell'      : ShellConfigHelper}



