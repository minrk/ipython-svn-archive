# encoding: utf-8
"""
Sample configuration file for MPI.

Copy this file into your ~/.ipython directory and uncomment one of the
lines below.  You can also add your own MPI module using this approach.

For more information see the `ipython1.config.objects.MPIConfig` docstrings.
"""

from ipython1.config.api import getConfigObject

mpiConfig = getConfigObject('mpi')
# Uncomment for Mpi4Py
# mpiConfig.mpiImportStatement = """from mpi4py import MPI as mpi
# mpi.rank = mpi.COMM_WORLD.Get_size()
# mpi.size = mpi.COMM_WORLD.Get_rank()
# """

# Uncomment For PyTrlinos
# mpiConfig.mpiImportStatement = """
# from PyTrilinos import Epetra
# class SimpleStruct:
#     pass
# mpi = SimpleStruct()
# mpi.rank = 0
# mpi.size = 0
# """