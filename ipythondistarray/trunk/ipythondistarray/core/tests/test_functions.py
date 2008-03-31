import unittest
import numpy as np
from numpy.testing.utils import assert_array_equal, assert_array_almost_equal

from ipythondistarray.core.error import *
from ipythondistarray.mpi.error import *
from ipythondistarray.mpi import mpibase
from ipythondistarray.mpi.mpibase import (
    MPI, 
    create_comm_of_size,
    create_comm_with_list)
from ipythondistarray.core import maps, distarray
from ipythondistarray.core import nulldistarray


class TestFunctions(unittest.TestCase):
    
    def test_arecompatible(self):
        """
        Test if two DistArrays are compatible.
        """
        try:
            comm = create_comm_of_size(4)
        except InvalidCommSizeError:
            pass
        else:
            if not comm==MPI.COMM_NULL:
                a = distarray.DistArray((16,16), dtype='int64', comm=comm)
                b = distarray.DistArray((16,16), dtype='float32', comm=comm)
                self.assertEquals(distarray.arecompatible(a,b), True)
                a = distarray.DistArray((16,16), dtype='int64', dist='c', comm=comm)
                b = distarray.DistArray((16,16), dtype='float32', dist='b', comm=comm)
                self.assertEquals(distarray.arecompatible(a,b), False)                
                comm.Free()
    
    def test_nullscompatible(self):
        """
        Make sure two null arrays are compatible.
        """
        a = nulldistarray.NullDistArray((16,16), dtype='int64')
        b = nulldistarray.NullDistArray((16,16), dtype='float32')
        self.assertEquals(distarray.arecompatible(a,b), True)
        a = nulldistarray.NullDistArray((16,16), dtype='int64', dist='c')
        b = nulldistarray.NullDistArray((16,16), dtype='float32', dist='b')
        self.assertEquals(distarray.arecompatible(a,b), False)  
    
    def test_mixedcompatible(self):
        """
        Make sure thata null and non-null array are not compatible.
        """
        try:
            comm = create_comm_of_size(4)
        except InvalidCommSizeError:
            pass
        else:
            if not comm==MPI.COMM_NULL:
                a = distarray.DistArray((16,16),dtype='int64', comm=comm)
                b = nulldistarray.NullDistArray((16,16))
                self.assertEquals(distarray.arecompatible(a,b), False)
                comm.Free()


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass