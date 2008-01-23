import unittest
import numpy as np
from numpy.testing.utils import assert_array_equal, assert_array_almost_equal
from ipythondistarray import maps, distarray
from ipythondistarray import mpibase

class TestInit(unittest.TestCase):
    
    def test_basic(self):
        da = distarray.DistArray((16,16), grid_shape=(4,))
        self.assertEquals(da.shape, (16,16))
        self.assertEquals(da.dist, {0:'b'})
        self.assertEquals(da.grid_shape,(4,))
        self.assertEquals(da.base_comm, mpibase.COMM_PRIVATE)
        self.assertEquals(da.comm_size, 4)
        self.assert_(da.comm_rank in range(4))
        self.assertEquals(da.ndistdim, 1)
        self.assertEquals(da.distdims, (0,))
        self.assertEquals(da.map_classes, (maps.BlockMap,))
        self.assertEquals(da.comm.Get_topo(), (da.grid_shape,(0,),(da.comm_rank,)))
        self.assertEquals(len(da.maps),1)
        self.assertEquals(da.maps[0].local_shape, 4)
        self.assertEquals(da.maps[0].shape, 16)
        self.assertEquals(da.maps[0].grid_shape, 4)
        self.assertEquals(da.local_shape,(4,))
        self.assertEquals(da.local_array.shape, da.local_shape)
        self.assertEquals(da.local_array.dtype, da.dtype)
        
    def test_localarray(self):
        da = distarray.DistArray((16,16), grid_shape=(4,))
        la = np.random.random(da.local_shape)
        la = np.asarray(la, dtype=da.dtype)
        da.set_localarray(la)
        assert_array_equal(la, da.get_localarray())

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
	

