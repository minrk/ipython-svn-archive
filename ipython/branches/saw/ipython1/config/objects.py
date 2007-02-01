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
#                           Benjamin Ragan-Kelley <benjaminrk@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

# Imports

from ipython1.config.base import Config

# Global defaults

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
    
from ipython1.kernel.enginepb import PBEngineClientFactory

class EngineConfig(Config):
    connectToControllerOn = {'ip': '127.0.0.1', 'port': enginePort}
    """The ip, port the controller is listening for engines on."""
    
    #engineClientProtocolInterface = IVanillaEngineClientFactory
    engineClientProtocolInterface = PBEngineClientFactory
    """The interface corresponding to the network protocol used to connect
    to the controller with."""


class MPIConfig(Config):
    """MPI Configuration information.
    
    The configuration for MPI is somewhat different from all the other
    configuration entities.  This is because the engine has to import
    a module that calls MPI_Init immediately upon starting - even before
    the command line options are parsed.  This means that the mpi setup
    cannot be controlled from the command line.  
    
    To get around this, ipengine does::
    
        config.updateConfigWithFile('mpirc.py')
    
    to get the MPi configuration information.  The mpirc.py file
    will be looked for in:
    
    1.  The cwd
    2.  The ~./ipython directory
    3.  In the IPYTHONDIR directory
    """

    mpiImportStatement = ''
    """The import statement that will be attempted in starting mpi.  
    
    Some common options are:
    
    - ``from mpi4py import MPI as mpi``:  For using mpi4py
    - ``from ipython1 import mpi``:  For using IPython1's basic MPI module.
      This module only calls MPI_Init and then defines mpi.rank and mpi.size.
      This is useful for the many cases you don't need the entire MPI API, 
      just to have a rank and size defined.  You could also probably use
      this approach to make MPI calls from C/C++ code.
      
    Users are free to make their own MPI modules to use in this way.  But
    those modules must to do things:
    
    1.  Call MPI_Init() in an appropriate manner upon being imported.
    2.  Define the size and rank attributes of the module.
    
    It is also a good idea to have MPI_Finalize called automatically when
    the Python interpreter is shut down.  For information about how to do
    this see the `ipython1.mpi` module or ``mpi4py``.
    """
    
# Controller configuration

from ipython1.kernel.enginevanilla import \
    IVanillaEngineServerFactory

from ipython1.kernel.multienginevanilla import \
    IVanillaControllerFactory
    
from ipython1.kernel.multienginepb import \
    IPBMultiEngineFactory

from ipython1.kernel.multienginexmlrpc import \
    IXMLRPCMultiEngineFactory
    
from ipython1.kernel.enginepb import \
    IPBEngineServerFactory

from ipython1.kernel.taskxmlrpc import \
    IXMLRPCTaskControllerFactory

class ControllerConfig(Config):
    #engineServerProtocolInterface = IVanillaEngineServerFactory
    engineServerProtocolInterface = IPBEngineServerFactory
    """The interface for the network protocol for talking to engines."""
    
    listenForEnginesOn  = {'ip': '', 'port': enginePort}
    """The ip and port to listen for engine on."""
    
    #clientInterfaces = [{'interface': IPBMultiEngineFactory, 
    #                     'ip': '', 
    #                     'port': 10111}]
    clientInterfaces = [{'interface': IVanillaControllerFactory, 
                         'ip': '', 
                         'port': clientVanillaPort},
                        {'interface': IPBMultiEngineFactory, 
                         'ip': '', 
                         'port': 10111},
                         {'interface': IXMLRPCMultiEngineFactory, 
                          'ip': '', 
                          'port': 10112}]
    # client interfaces for taskcontroller
    taskClientInterfaces = [{'interface':IXMLRPCTaskControllerFactory,
                        'ip':'',
                        'port':10113}]
    serveTasks = False
    """A list of interface, ip, and port for the protocols used to talk to clients.
    
    The ip and port for each interface determines what ip and port the 
    controller will listen on with that network protocol.
    """

# Client configuration

from ipython1.kernel.multienginevanilla import \
    RemoteController

class ClientConfig(Config):    
    RemoteController = RemoteController
    """The RemoteController class to use.
    
    This allow new RemoteController classes that use different network
    protocols to be used.
    """

    connectToControllerOn = {'ip': '127.0.0.1', 'port': clientVanillaPort}
    """The (ip, port) tuple the client will use to connect to the controller."""
    

# All top-level config classes must be listed here.

configClasses = {'engine'     : EngineConfig,
                 'controller' : ControllerConfig,
                 'client'     : ClientConfig,
                 'shell'      : ShellConfig,
                 'mpi'        : MPIConfig}



