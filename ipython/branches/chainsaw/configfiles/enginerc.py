#!/usr/bin/env python
# encoding: utf-8
"""
enginerc.py
"""

# Get a valid configuration object for the engine

from ipython1.config.api import getConfigObject 

enginerc = getConfigObject('engine')

# Now we can configure the engine

from ipython1.kernel.enginevanilla import \
    IVanillaEngineClientFactory
    
from ipython1.core.shell import InteractiveShell
    
# Set the IP and port that the controller is listening on for Engines
enginerc.connectToControllerOn = ('127.0.0.1', 10201)

# Set the network protocol used to talk to the controller
enginerc.engineClientProtocolInterface = IVanillaEngineClientFactory

# Set the maxMessageSize in bytes
#enginerc.maxMessageSize = 99999999
enginerc.maxMessageSize = 1010101

# Set the import statement to use in starting mpi
#enginerc.mpiImportStatement = 'from mpi4py import MPI as mpi'
#enginerc.mpiImportStatement = 'from ipython1.kernel import mpi'

