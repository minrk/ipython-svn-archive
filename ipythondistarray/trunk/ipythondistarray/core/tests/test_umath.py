import numpy as np

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
from ipythondistarray.core.nulldistarray import (
    allnull, 
    anynull, 
    nonenull,
    NullDistArray,
    null_like)


class TestUnaryUFunc(unittest.TestCase):
    
    def test_basic(self):
        """
        See if unary ufunc works for a DistArray.
        """
        try:
            comm = create_comm_of_size(4)
        except InvalidCommSizeError:
            pass
        else:
            if not comm==MPI.COMM_NULL:
                a = distarray.DistArray((16,16), dtype='int32', comm=comm)
                a.fill(1)
                b = distarray.negative(a)
                if nonenull(a, b):
                    self.assert_(np.all(a.local_array==-b.local_array))
                b = distarray.empty_like(a)
                b = distarray.negative(a, b)
                if nonenull(a, b):
                    self.assert_(np.all(a.local_array==-b.local_array))
                a = distarray.DistArray((16,16), dtype='int32', comm=comm)
                b = distarray.DistArray((20,20), dtype='int32', comm=comm)
                self.assertRaises(IncompatibleArrayError, distarray.negative, b, a)
    
    def test_nullnull(self):
        """
        See if a unary ufunc works for a NullDistArray.
        """
        a = NullDistArray((16,16), dtype='int32')
        a.fill(1)
        b = distarray.negative(a)
        self.assert_(b.isnull())
        b = null_like(a)
        b = distarray.negative(a, b)
        self.assert_(b.isnull())
        a = NullDistArray((16,16), dtype='int32')
        b = NullDistArray((20,20), dtype='int32')
        self.assertRaises(IncompatibleArrayError, distarray.negative, b, a)
    
    def test_incompatible_result(self):
        """
        An error should be raised if arrays have opposite nullity.
        """
        try:
            comm = create_comm_of_size(4)
        except InvalidCommSizeError:
            pass
        else:
            a = distarray.DistArray((16,16), dtype='int32', comm=comm)
            a.fill(1)
            b = NullDistArray((16,16), dtype='int32')
            if not a.isnull() and b.isnull():           
                self.assertRaises(IncompatibleArrayError, distarray.negative, a, b)
                self.assertRaises(IncompatibleArrayError, distarray.negative, b, a)


class TestBinaryUFunc(unittest.TestCase):
    
    def test_basic(self):
        """
        See if binary ufunc works for a DistArray.
        """
        try:
            comm = create_comm_of_size(4)
        except InvalidCommSizeError:
            pass
        else:
            if not comm==MPI.COMM_NULL:
                a = distarray.DistArray((16,16), dtype='int32', comm=comm)
                b = distarray.DistArray((16,16), dtype='int32', comm=comm)
                a.fill(1)
                b.fill(1)
                c = distarray.add(a, b)
                if nonenull(a, b, c):
                    self.assert_(np.all(c.local_array==2))
                c = distarray.empty_like(a)
                c = distarray.add(a, b, c)
                if nonenull(a, b, c):
                    self.assert_(np.all(c.local_array==2))
                a = distarray.DistArray((16,16), dtype='int32', comm=comm)
                b = distarray.DistArray((20,20), dtype='int32', comm=comm)
                self.assertRaises(IncompatibleArrayError, distarray.add, a, b)
                a = distarray.DistArray((16,16), dtype='int32', comm=comm)
                b = distarray.DistArray((16,16), dtype='int32', comm=comm)
                c = distarray.DistArray((20,20), dtype='int32', comm=comm)
                self.assertRaises(IncompatibleArrayError, distarray.add, a, b, c)
    
    def test_nullnull(self):
        """
        See if a binary ufunc works for a NullDistArray.
        """
        a = NullDistArray((16,16), dtype='int32')
        b = NullDistArray((16,16), dtype='int32')
        a.fill(1)
        b.fill(1)
        c = distarray.add(a, b)
        self.assert_(c.isnull())
        c = null_like(a)
        c = distarray.add(a, b, c)
        self.assert_(c.isnull())
        a = NullDistArray((16,16), dtype='int32')
        b = NullDistArray((20,20), dtype='int32')
        self.assertRaises(IncompatibleArrayError, distarray.add, b, a)
        a = NullDistArray((16,16), dtype='int32')
        b = NullDistArray((16,16), dtype='int32')
        b = NullDistArray((20,20), dtype='int32')
        self.assertRaises(IncompatibleArrayError, distarray.add, a, b, c)
    
    def test_incompatible_result(self):
        """
        An error should be raised if arrays have opposite nullity.
        """
        try:
            comm = create_comm_of_size(4)
        except InvalidCommSizeError:
            pass
        else:
            a = distarray.DistArray((16,16), dtype='int32', comm=comm)
            b = distarray.DistArray((16,16), dtype='int32', comm=comm)
            a.fill(1)
            b.fill(1)
            c = NullDistArray((16,16), dtype='int32')
            if nonenull(a, b) and c.isnull():           
                self.assertRaises(IncompatibleArrayError, distarray.add, a, b, c)
                self.assertRaises(IncompatibleArrayError, distarray.add, c, a, b)
                self.assertRaises(IncompatibleArrayError, distarray.add, a, c, a)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass