
# encoding: utf-8
"""
Sample configuration file for MPI.

Copy this file into your ~/.ipython directory and uncomment one of the
lines below.  You can also add your own MPI module using this approach.

For more information see the `ipython1.config.objects.MPIConfig` docstrings.
"""

from ipython1.config.api import getConfigObject

mpiConfig = getConfigObject('mpi')
I
# For IPython's basic mpi module.  This only calls MPI_Init
# and then defines mpi.rank and mpi.size.  This is useful
# for the many cases where you just need to know those two things.
# You could also probably use this approach to make MPI calls from 
# C/C++ code.
#mpiConfig.mpiImportStatement = 'from ipython1 import mpi'

# For using mpi4py
#mpiConfig.mpiImportStatement = 'from mpi4py import MPI as mpi'
