import unittest
import numpy as np
from mpi4py import MPI
from numpy.testing.utils import assert_array_equal, assert_array_almost_equal

from ipythondistarray import maps, distarray
from ipythondistarray import mpibase, utils

def create_comm(size=4):

    group = mpibase.COMM_PRIVATE.Get_group()
    comm_size = mpibase.COMM_PRIVATE.Get_size()
    if size > comm_size:
        return MPI.COMM_NULL
    else:
        subgroup = group.Incl(range(size))
        newcomm = mpibase.COMM_PRIVATE.Create(subgroup)
        return newcomm
    
class TestInit(unittest.TestCase):
    
    def test_basic(self):
        comm = create_comm(4)
        if not comm==MPI.COMM_NULL:
            da = distarray.DistArray((16,16), grid_shape=(4,),comm=comm)
            self.assertEquals(da.shape, (16,16))
            self.assertEquals(da.dist, ('b',None))
            self.assertEquals(da.grid_shape,(4,))
            self.assertEquals(da.base_comm, comm)
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
            comm.Free()
        
    def test_localarray(self):
        comm = create_comm(4)
        if not comm==MPI.COMM_NULL:
            da = distarray.DistArray((16,16), grid_shape=(4,),comm=comm)
            la = np.random.random(da.local_shape)
            la = np.asarray(la, dtype=da.dtype)
            da.set_localarray(la)
            assert_array_equal(la, da.get_localarray())
            comm.Free()

    def test_grid_shape(self):
        comm = create_comm(12)
        if not comm==MPI.COMM_NULL:
            da = distarray.DistArray((20,20),dist='b',comm=comm)
            self.assertEquals(da.grid_shape,(3,4))
            da = distarray.DistArray((2*10,6*10),dist='b',comm=comm)
            self.assertEquals(da.grid_shape,(2,6))
            da = distarray.DistArray((6*10,2*10),dist='b',comm=comm)
            self.assertEquals(da.grid_shape,(6,2))
            da = distarray.DistArray((100,10,300),dist=('b',None,'c'),comm=comm)
            self.assertEquals(da.grid_shape,(2,6))
            da = distarray.DistArray((100,50,300),dist='b',comm=comm)
            self.assertEquals(da.grid_shape,(2,2,3))                  
            comm.Free()

class TestDistMatrix(unittest.TestCase):

    def test_plot_dist_matrix(self):
        comm = create_comm(12)
        if not comm==MPI.COMM_NULL:
            da = distarray.DistArray((10,10), dist=('c','c'),comm=comm)
            a = da.get_dist_matrix()
            if comm.Get_rank()==0:
                import pylab
                pylab.ion()
                pylab.matshow(a)
                pylab.colorbar()
                pylab.draw() 
                pylab.show()
            comm.Free()

class TestLocalInd(unittest.TestCase):
    
    def test_block(self):
        comm = create_comm(4)
        if not comm==MPI.COMM_NULL:
            da = distarray.DistArray((4,4),comm=comm)
            self.assertEquals(da.shape,(4,4))
            self.assertEquals(da.grid_shape,(4,))
            row_result = [(0,0),(0,1),(0,2),(0,3)]
            for row in range(da.shape[0]):
                calc_row_result = [da.local_ind(row,col) for col in range(da.shape[1])]
                self.assertEquals(row_result, calc_row_result)
            comm.Free()
            
    def test_cyclic(self):
        comm = create_comm(4)
        if not comm==MPI.COMM_NULL:
            da = distarray.DistArray((8,8),dist={0:'c'},comm=comm)
            self.assertEquals(da.shape,(8,8))
            self.assertEquals(da.grid_shape,(4,))
            self.assertEquals(da.map_classes, (maps.CyclicMap,))
            result = utils.outer_zip(4*(0,)+4*(1,),range(8))
            calc_result = [[da.local_ind(row,col) for col in range(da.shape[1])] for row in range(da.shape[0])]
            self.assertEquals(result,calc_result)
            comm.Free()

class TestGlobalInd(unittest.TestCase):
    
    def round_trip(self, da):
        for indices in utils.multi_for( [xrange(s) for s in da.shape] ):
            li = da.local_ind(*indices)
            owner_rank = da.owner_rank(*indices)
            gi = da.global_ind_by_rank(owner_rank,*li)
            self.assertEquals(gi,indices)
    
    def test_block(self):
        comm = create_comm(4)
        if not comm==MPI.COMM_NULL:
            da = distarray.DistArray((4,4),comm=comm)
            self.round_trip(da)
            comm.Free()
             
    def test_cyclic(self):
        comm = create_comm(4)
        if not comm==MPI.COMM_NULL:
            da = distarray.DistArray((8,8),dist=('c',None),comm=comm)
            self.round_trip(da)
            comm.Free()

    def test_crazy(self):
        comm = create_comm(4)
        if not comm==MPI.COMM_NULL:
            da = distarray.DistArray((10,100,20),dist=('b','c',None),comm=comm)
            self.round_trip(da)
            comm.Free()

                

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
	

