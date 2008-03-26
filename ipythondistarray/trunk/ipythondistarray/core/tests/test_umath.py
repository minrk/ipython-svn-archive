import numpy as np

import unittest
import numpy as np
from numpy.testing.utils import assert_array_equal, assert_array_almost_equal

from ipythondistarray.mpi import mpibase
MPI = mpibase.MPI

from ipythondistarray.core.error import *
from ipythondistarray.core import maps, distarray

class TestUFuncs(unittest.TestCase):
    
    def test_add(self):
        """
        Test the add function.
        """
        comm = create_comm(4)
        if not comm==MPI.COMM_NULL:
            a = distarray.DistArray((16,16), dtype='int32', comm=comm)
            b = distarray.DistArray((16,16), dtype='int32', comm=comm)
            a.fill(1)
            b.fill(1)
            c = distarray.add(a, b)
            self.assert_(np.all(c.local_array==2))
            c = distarray.empty_like(a)
            c = distarray.add(a, b, c)
            self.assert_(np.all(c.local_array==2))
    
    def test_add_error(self):
        """
        Add should raise if arrays are not compatible.
        """
        comm = create_comm(4)
        if not comm==MPI.COMM_NULL:
            a = distarray.DistArray((16,16), dist=('b',None), dtype='int32', comm=comm)
            b = distarray.DistArray((16,16), dist=(None,'b'), dtype='int32', comm=comm)
            self.assertRaises(IncompatibleArrayError, distarray.add, a, b)



if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass