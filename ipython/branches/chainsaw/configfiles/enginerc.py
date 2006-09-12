#!/usr/bin/env python
# encoding: utf-8
"""
enginerc.py
"""

# Imports

from ipython1.kernel.enginevanilla import \
    IVanillaEngineClientFactory
    
from ipython1.core.shell import InteractiveShell

# Example configuration settings
    
# Set the IP and port that the controller is listening on for Engines
#EngineConfig.connectToControllerOn = ('127.0.0.1', 10201)

# Set the network protocol used to talk to the controller
#EngineConfig.engineClientProtocolInterface = IVanillaEngineClientFactory

# Set the InteractiveShell class to use in the Engine
#EngineConfig.engineShell = InteractiveShell

# Set the maxMessageSize in bytes
#EngineConfig.maxMessageSize = 99999999

# Set the import statement to use in starting mpi
#EngineConfig.mpiImportStatement = 'from mpi4py import MPI as mpi'
#EngineConfig.mpiImportStatement = 'from ipython1.kernel import mpi'

