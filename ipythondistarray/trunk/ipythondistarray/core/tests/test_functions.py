import unittest
import numpy as np
from numpy.testing.utils import assert_array_equal, assert_array_almost_equal

from ipythondistarray.mpi import mpibase
MPI = mpibase.MPI

from ipythondistarray.core import maps, distarray

class TestFunctions(unittest.TestCase):
    
    def test_arecompatible(self):
        """
        Test if two DistArrays are compatible.
        """
        comm = create_comm(4)
        if not comm==MPI.COMM_NULL:
            a = distarray.DistArray((16,16),dtype='int64', comm=comm)
            b = distarray.DistArray((16,16),dtype='float32', comm=comm)
            self.assertEquals(distarray.arecompatible(a,b), True)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass