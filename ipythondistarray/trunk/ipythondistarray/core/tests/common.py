import unittest
import numpy as np
from mpi4py import MPI
from numpy.testing.utils import assert_array_equal, assert_array_almost_equal

from ipythondistarray.mpi import mpibase

def create_comm(size=4):

    group = mpibase.COMM_PRIVATE.Get_group()
    comm_size = mpibase.COMM_PRIVATE.Get_size()
    if size > comm_size:
        return MPI.COMM_NULL
    else:
        subgroup = group.Incl(range(size))
        newcomm = mpibase.COMM_PRIVATE.Create(subgroup)
        return newcomm