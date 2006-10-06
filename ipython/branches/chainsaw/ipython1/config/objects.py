#!/usr/bin/env python
# encoding: utf-8
"""
Configuration objects for IPython.

This module contains classes that contain configuration information.  These
classes are subclasses of `base.Config` and define specific attributes that
are needed to configure a particular entity.  

These classes should not be instantiated directly by a user or developer.  
Instead, `api.getConfigObject` should be used to retrieve an instance.  
This ensures that only one config object of each class gets created in 
a given process.

The configuration objects are retrieved by key. A complete list of the classes 
and corresponding keys can be found at the bottom of this file in the 
`configClasses` dictionary.
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

from ipython1.config.base import Config

# Global defaults
    
maxMesageSize = 99999999
enginePort = 10201
clientVanillaPort = 10105

# Shell configuration

from ipython1.core.shell import InteractiveShell

class ShellConfig(Config):
    shellClass = InteractiveShell
    """The particular shell class to use.
    
    Right now there is only one: `core.InteractiveShell`, but by creating a 
    new shell class that implements the same api as this default the user
    can customize its behavior.  For instance, the user could make a shell
    that supports additional syntax.
    """

    filesToRun = []
    """A list of local files the shell should run upon starting."""

# Engine configrations

from ipython1.kernel.enginevanilla import \
    IVanillaEngineClientFactory

class EngineConfig(Config):
    connectToControllerOn = ('127.0.0.1', enginePort)
    """The (ip, port) the controller is listening for engines on."""
    
    engineClientProtocolInterface = IVanillaEngineClientFactory
    """The interface corresponding to the network protocol used to connect
    to the controller with."""

    maxMessageSize = maxMesageSize
    """The maximum message size supported by the network protocol."""

    mpiImportStatement = ''
    """The import statement that will be attempted in starting mpi.  
    
    Some common options are:
    
    - ``from mpi4py import MPi as mpi``
    - ``from ipython1 import mpi``
    """
    
# Controller configuration

from ipython1.kernel.enginevanilla import \
    IVanillaEngineServerFactory

from ipython1.kernel.controllervanilla import \
    IVanillaControllerFactory
    
from ipython1.kernel.controllerpb import \
    IPBControllerFactory
    
class ControllerConfig(Config):
    engineServerProtocolInterface = IVanillaEngineServerFactory
    """The interface for the network protocol for talking to engines."""
    
    listenForEnginesOn  = ('', enginePort)
    """The (ip, port) to listen for engine on."""
    
    clientInterfaces = [(IVanillaControllerFactory, ('', clientVanillaPort)),
                        (IPBControllerFactory, ('', 10111))]
    """A list of (interfaces, (ip,port)) for the protocols used to talk to clients.
    
    The (ip,port) tuple for each interface determines what ip and port the 
    controller will listen on with that network protocol.
    """
    
    maxMessageSize = maxMesageSize
    """The maximum message size supported by the network protocol."""
    
# Client configuration

from ipython1.kernel.controllervanilla import \
    RemoteController

class ClientConfig(Config):    
    RemoteController = RemoteController
    """The RemoteController class to use.
    
    This allow new RemoteController classes that use different network
    protocols to be used.
    """

    connectToControllerOn = ('127.0.0.1', clientVanillaPort)
    """The (ip, port) tuple the client will use to connect to the controller."""
    
    maxMessageSize = maxMesageSize
    """The maximum message size supported by the network protocol."""

# All top-level config classes must be listed here.

configClasses = {'engine'     : EngineConfig,
                 'controller' : ControllerConfig,
                 'client'     : ClientConfig,
                 'shell'      : ShellConfig}



