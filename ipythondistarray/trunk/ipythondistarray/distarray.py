from mpi4py import MPI
import numpy as np

from ipythondistarray import mpibase
from ipythondistarray import maps
from ipythondistarray import utils


class InvalidBaseCommError(Exception):
    pass

class InvalidGridShapeError(Exception):
    pass

class GridShapeError(Exception):
    pass

class DistError(Exception):
    pass

class DistArray(object):
    
    def __init__(self, shape, dist={0:'b'}, dtype=float, grid_shape=None,
                 comm=None):
        """Create a distributed memory array on a set of processors.
        """
        self.ndim = len(shape)
        self.shape = shape
        self.dist = dist
        self.dtype = np.dtype(dtype)
        self.grid_shape = grid_shape
        self.base_comm = comm
        self.comm = None
        
        # This order is extremely important!
        self._init_base_comm()
        self._init_map_classes()
        self._init_grid_shape()
        self._init_comm()
        self._init_maps()
        self._allocate()
             
    def __del__(self):
        if self.comm is not None:
            self.comm.Free()
             
    def _init_base_comm(self):
        if self.base_comm==MPI.COMM_NULL:
            raise MPICommError("Cannot create a DistArray with a MPI_COMM_NULL")
        elif self.base_comm is None:
            self.base_comm = mpibase.COMM_PRIVATE
        elif isinstance(self.base_comm, MPI.Comm):
            pass
        else:
            raise InvalidBaseCommError("Not an MPI.Comm instance")
        self.comm_size = self.base_comm.Get_size()
        self.comm_rank = self.base_comm.Get_rank()
        
    def _init_map_classes(self):
        dist = self._canonical_dist_form(self.dist)
        reduced_dist = [d for d in dist if d is not None]
        ndistdim = len(reduced_dist)
        if ndistdim > self.ndim:
            raise DistError("Too many distributed dimensions")
        distdims = [i for i in range(self.ndim) if dist[i] is not None]
        map_classes = [self._get_map_class(d) for d in reduced_dist]
        self.ndistdim = ndistdim
        self.distdims = tuple(distdims)
        self.map_classes = tuple(map_classes)
        self.dist = tuple(dist)
            
    def _canonical_dist_form(self, dist):
        if isinstance(dist, str):
            return self.ndim*(dist)
        elif isinstance(dist, (list, tuple)):
            return tuple(dist)
        elif isinstance(dist, dict):
            return tuple([dist.get(i) for i in range(self.ndim)])
        else:
            DistError("dist must be a string, tuple/list or dict")        
            
    def _get_map_class(self, code):
        return maps.get_map_class(code)
        
    def _init_grid_shape(self):
        if self.grid_shape is None:
            self._optimize_grid_shape()
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
        if self.ndistdim==1:
            self.grid_shape = (self.comm_size,)
        else:
            factors = utils.create_factors(self.comm_size, self.ndistdim)
            if factors != []:
                reduced_shape = [self.shape[i] for i in self.distdims]
                factors = [utils.mirror_sort(f, reduced_shape) for f in factors]
                rs_ratio = self._compute_grid_ratios(reduced_shape)
                f_ratios = [self._compute_grid_ratios(f) for f in factors]
                distances = [rs_ratio-f_ratio for f_ratio in f_ratios]
                norms = np.array([np.linalg.norm(d,2) for d in distances])
                index = norms.argmin()
                self.grid_shape = tuple(factors[index])
            else:
                raise GridShapeError("Cannot distribute array over processors")
        
    def _compute_grid_ratios(self, shape):
        n = len(shape)
        return np.array([float(shape[i])/shape[j] for i in range(n) for j in range(n) if i < j])
        
    def _init_comm(self):
        self.comm = self.base_comm.Create_cart(self.grid_shape,
            self.ndistdim*(False,), False)
        self.cart_coords = self.comm.Get_coords(self.comm_rank) 
                
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
        
    def owner(self, *args):
        indices = args
        owners = [self.maps[i].owner(indices[self.distdims[i]]) for i in range(self.ndistdim)]
        return self.comm.Get_rank(owners)
        
    def _print_distribution(self):
        print "HI"
        if self.ndim==2:
            a = numpy.empty(self.shape,dtype=int)
            for i in range(shape[0]):
                for j in range(shape[1]):
                    a[i,j] = self.owner(i,j)
            print a
        
            
        
      
        
 
    
        
    
        


