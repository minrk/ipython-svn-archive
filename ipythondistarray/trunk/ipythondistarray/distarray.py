from mpi4py import MPI
import numpy as np

from ipythondistarray import mpibase
from ipythondistarray import maps
from ipythondistarray import utils


class InvalidBaseCommError(Exception):
    pass

class InvalidGridShapeError(Exception):
    pass


class DistArray(object):
    
    def __init__(self, shape, dist={0:'b'}, dtype=float, comm=None,
                 grid_shape=None):
                 
        """Create a distributed memory array.
        
        dist = {0:'b',2:'c',3:'bc'}
        """
        self.ndim = len(shape)
        self.shape = shape
        self.dist = dist
        self.dtype = np.dtype(dtype)
        self.ndistdim = len(self.dist.keys())
        self.grid_shape = grid_shape
        self.base_comm = comm
        self.comm = None
        
        self._init_base_comm()
        self._init_grid_shape()
        self._init_comm()
        self._init_map_classes()
        self._init_maps()
        self._allocate()
             
    def __del__(self):
        if self.comm is not None:
            self.comm.Free()
             
    def _init_base_comm(self):
        if self.base_comm is None:
            self.base_comm = mpibase.COMM_PRIVATE
        elif isinstance(self.base_comm, MPI.Comm):
            pass
        else:
            raise InvalidBaseCommError("Not an MPI.Comm instance")
        self.comm_size = self.base_comm.Get_size()
        self.comm_rank = self.base_comm.Get_rank()
        
    def _init_grid_shape(self):
        if self.grid_shape is None:
            self.grid_shape = _optimize_grid_shape()
        else:
            try:
                self.grid_shape = tuple(self.grid_shape)
            except:
                raise InvalidGridShapeError("grid_shape not castable to a tuple")
            if len(self.grid_shape)!=self.ndistdim:
                raise InvalidGridShapeError("grid_shape has the wrong length")
            ngriddim = reduce(lambda x,y: x*y, self.grid_shape)
            if ngriddim != self.comm_size:
                raise InvalidGridShapeError("grid_shape is incompatible with the number of processors")
        
    def _optimize_grid_shape(self):
        factors = utils.create_factors(self.comm_size, self.ndistdim)
        reduced_shape = [shape[i] for i in self.distdims]
        factors = [utils.similarity_sort(f, reduced_shape) for f in factors]
        
    def _init_comm(self):
        self.comm = self.base_comm.Create_cart(self.grid_shape,
            self.ndistdim*(False,), False)
        self.cart_coords = self.comm.Get_coords(self.comm_rank) 
        
    def _init_map_classes(self):
        map_list = []
        distdims = []
        for k, v in self.dist.iteritems():
            distdims.append(k)
            map_list.append(self._get_map_class(v))
        self.distdims = tuple(distdims)
        self.map_classes = tuple(map_list)
            
    def _get_map_class(self, code):
        return maps.get_map_class(code)
        
    def _init_maps(self):
        maps = []
        local_shape = []
        for i, distdim in enumerate(self.distdims):
            minst = self.map_classes[i](self.shape[distdim], self.grid_shape[i])
            local_shape.append(minst.local_shape)
            maps.append(minst)
        self.maps = tuple(maps)
        self.local_shape = tuple(local_shape)
        
    def _allocate(self):
        self.local_array = np.empty(self.local_shape, dtype=self.dtype)
        
    def get_localarray(self):
        return self.local_array
        
    def set_localarray(self, a):
        a = np.asarray(a, dtype=self.dtype, order='C')
        if a.shape != self.local_shape:
            raise ValueError("incompatible local array shape")
        self.local_array = a
        
            
        
      
        
 
    
        
    
        


