import unittest
import numpy as np
from numpy.testing.utils import assert_array_equal, assert_array_almost_equal

from ipythondistarray.core.error import *
from ipythondistarray.mpi import mpibase
from ipythondistarray.mpi.mpibase import MPI
from ipythondistarray.core.nulldistarray import NullDistArray, null_like, isnull

class TestNullDistArray(unittest.TestCase):
    
    def test_create(self):
        """
        Can we create a NullDistArray?
        """
        a = NullDistArray((10,10))
        self.assert_(isinstance(a, NullDistArray))
        self.assertEquals(a.isnull(), True)
        self.assertEquals(a._shape, (10,10))
        self.assertEquals(a._ndim, 2)
        self.assertEquals(a._dtype, np.dtype(float))
        self.assertEquals(a._size, reduce(lambda x,y: x*y, a._shape))
        self.assertEquals(a._itemsize, np.dtype(float).itemsize)
        self.assertEquals(a.comm, MPI.COMM_NULL)
        def tryit():
            a = NullDistArray((10,10), comm=mpibase.COMM_PRIVATE)
        self.assertRaises(InvalidBaseCommError, tryit)
    
    
    def test_goodattrs(self):
        """
        Can we get the good attributes?
        """
        a = NullDistArray((10,10), dtype='float32')
        self.assertEquals(a.comm, MPI.COMM_NULL)
        self.assertEquals(a.base_comm, MPI.COMM_NULL)
    
    
    def test_badattrs(self):
        """
        A get on other attributes should raise.
        """
        a = NullDistArray((10,10), dtype='float32')
        self.assertRaises(NullArrayAttributeError, getattr, a, 'dist')
        self.assertRaises(NullArrayAttributeError, getattr, a, 'ndistdim')
        self.assertRaises(NullArrayAttributeError, getattr, a, 'grid_shape')
        self.assertRaises(NullArrayAttributeError, getattr, a, 'shape')
        self.assertRaises(NullArrayAttributeError, getattr, a, 'dtype')
        self.assertRaises(NullArrayAttributeError, getattr, a, 'ndim')    
    
    def test_null_like(self):
        """
        Make sure that null_like creates a similar NullDistArray.
        """
        a = NullDistArray((10,10), dtype='float32')
        b = null_like(a)
        self.assertEquals(a.base_comm, b.base_comm)
        self.assertEquals(a.comm, b.comm)
        self.assertEquals(a._shape, b._shape)
        self.assertEquals(a._ndim, b._ndim)
        self.assertEquals(a._dtype, b._dtype)
        self.assertEquals(a._grid_shape, b._grid_shape)

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass