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
__docformat__ = "restructuredtext en"
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelley <benjaminrk@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

from ipython1.config.base import Config

#-------------------------------------------------------------------------------
# Default Port Values
#-------------------------------------------------------------------------------

enginePort = 10201

pbMEPort = 10111
xmlrpcMEPort = 10112
vanillaMEPort = 10105
pbTCPort = 10114
xmlrpcTCPort = 10113
httpMEPort = 8080

#-------------------------------------------------------------------------------
# Shell Configuration
#-------------------------------------------------------------------------------

from ipython1.core.shell import InteractiveShell

class ShellConfig(Config):
    shellClass = InteractiveShell
    """The particular shell class to use.
    
    Right now there is only one: `core.InteractiveShell`, but by creating a 
    new shell class that implements the same api as this default the user
    can customize its behavior.  For instance, the user could make a shell
    that supports additional syntax.
    """
    
    shellImportStatement = ''
    
#-------------------------------------------------------------------------------
# Engine Configuration
#-------------------------------------------------------------------------------

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
    
    to get the MPI configuration information.  The mpirc.py file
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
    
#-------------------------------------------------------------------------------
# Controller Configuration
#-------------------------------------------------------------------------------

# from ipython1.kernel.enginevanilla import \
#     IVanillaEngineServerFactory
# 
# from ipython1.kernel.multienginevanilla import \
#     IVanillaControllerFactory
#     
# from ipython1.kernel.multienginepb import \
#     IPBMultiEngineFactory
# 
from ipython1.kernel.multienginexmlrpc import \
    IXMLRPCMultiEngineFactory
    
from ipython1.kernel.multienginehttp import \
    IHTTPMultiEngineFactory
    
from ipython1.kernel.enginepb import \
    IPBEngineServerFactory

from ipython1.kernel.taskxmlrpc import \
    IXMLRPCTaskControllerFactory

from ipython1.kernel.taskpb import \
    IPBTaskControllerFactory

from ipython1.kernel.multiengine import IMultiEngine
from ipython1.kernel.task import ITaskController


# pbME = {'interface': IPBMultiEngineFactory, 
#         'ip': '', 
#         'port': pbMEPort}
xmlrpcME = {'interface': IXMLRPCMultiEngineFactory, 
            'ip': '', 
            'port': xmlrpcMEPort}
# vanillaME = {'interface': IVanillaControllerFactory, 
#              'ip': '', 
#              'port': vanillaMEPort}
httpME = {'interface': IHTTPMultiEngineFactory, 
          'ip': '', 
          'port': httpMEPort}
networkInterfacesME = {'http': httpME, 'xmlrpc':xmlrpcME}
# Uncomment this to expose to multiple network interfaces
#networkInterfacesME = {'pb': pbME, 'xmlrpc': xmlrpcME}

pbTC = {'interface':IPBTaskControllerFactory,
        'ip':'',
        'port':pbTCPort}
xmlrpcTC = {'interface':IXMLRPCTaskControllerFactory,
            'ip':'',
            'port':xmlrpcTCPort}
networkInterfacesTC = {'pb': pbTC}
# Uncomment this to expose to multiple network interfaces
#networkInterfacesTC = {'pb': pbTC, 'xmlrpc': xmlrpcTC}


class ControllerConfig(Config):
    #engineServerProtocolInterface = IVanillaEngineServerFactory
    engineServerProtocolInterface = IPBEngineServerFactory
    """The interface for the network protocol for talking to engines."""
    
    listenForEnginesOn  = {'ip': '', 'port': enginePort}
    """The ip and port to listen for engine on."""
   
    controllerInterfaces = {'multiengine': {'controllerInterface': IMultiEngine, 
                                            'networkInterfaces': networkInterfacesME,
                                            'default': 'pb'},
                            'task' : {'controllerInterface': ITaskController, 
                                      'networkInterfaces': networkInterfacesTC,
                                      'default': 'pb'}}
    """Specify what how the controller is exposed.
    
    :Parameters:
        - `default`: for each controller interface determines which network
          interface will be controlled by command-line flags to ipcontroller.
    """
                                      
    controllerImportStatement = ''


#-------------------------------------------------------------------------------
# Client Configuration
#-------------------------------------------------------------------------------

from ipython1.kernel.multienginevanilla import \
    RemoteController

# from ipython1.kernel.multienginepb import PBInteractiveMultiEngineClient

from ipython1.kernel.taskpb import PBConnectingTaskClient

class ClientConfig(Config):    
    # RemoteController = PBInteractiveMultiEngineClient
    """The RemoteController class to use.
    
    This allow new RemoteController classes that use different network
    protocols to be used.
    """

    connectToRemoteControllerOn = {'ip': '127.0.0.1', 'port': pbMEPort}
    """The (ip, port) tuple the client will use to connect to the controller."""
    
    TaskController = PBConnectingTaskClient
    
    connectToTaskControllerOn = {'ip': '127.0.0.1', 'port': pbTCPort}
    

# All top-level config classes must be listed here.

configClasses = {'engine'     : EngineConfig,
                 'controller' : ControllerConfig,
                 'client'     : ClientConfig,
                 'shell'      : ShellConfig,
                 'mpi'        : MPIConfig}



