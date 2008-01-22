import numpy as np
from ipythondistarray import mpicore
from mpi4py import MPI

class Map(object):
    
    def __init__(self, nglobal, nprocs):
        self.nglobal = nglobal
        self.nprocs = nprocs
        self.nlocal = self.nglobal/self.nprocs
        if self.nglobal%self.nprocs > 0:
            self.nlocal += 1
    
    def owner(self, global_i):
        raise NotImplemented("implement in sublcass")
        
    def local_i(self, global_i):
        raise NotImplemented("implement in sublcass")
        
    def global_i(self, owner, local_i):
        raise NotImplemented("implement in sublcass")


class BlockMap(Map):
        
    def owner(self, global_i):
        return global_i/self.nlocal
        
    def local_i(self, global_i):
        local_i = global_i%self.nprocs
        return self.owner(global_i), local_i
        
    def global_i(self, owner, local_i):
        return owner*self.nlocal + local_i

class CyclicMap(Map):
    
    def owner(self, global_i):
        return global_i%self.nprocs
    
    def local_i(self, global_i):
        local_i = global_i/self.nprocs
        return self.owner(global_i), local_i
        
    def global_i(self, owner, local_i):
        return owner + local_i*self.nlocal

class BlockCyclicMap(Map):
    pass

bp1 = BlockMap(16, 2)
bp2 = CyclicMap(16, 2)

import numpy
result = numpy.empty((16,16),dtype='int32')

grid = numpy.arange(4, dtype='int32')
grid.shape=(2,2)

for i in range(16):
    for j in range(16):
        # print bp1.owner(i), bp2.owner(j)
        result[i,j] = grid[bp1.owner(i), bp2.owner(j)] 

# print result

# shape 
# # of processors [0,...,N-1]
# Which dims are dist
# processor grid for load balancing
# Maps
# (2, 4*b, 6*b) -> processor grid
# 

def factor2(n):
    intn = int(n)
    factors = []
    i = 0

    # 1 is a special case
    if n == 1:
        return [(1,1)]

    while 1:
        i += 1

        if i > n:
            break

        if n % i == 0:
            # if n/i not in factors.keys():
            factors.append((i, n/i))

    return factors

class InvalidBaseCommError(Exception):
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
        self.ndistdim = len(keys(self.dist))
        self.grid_shape = grid_shape
        self.base_comm = comm
        self.comm = None
        
        self._init_base_comm()
        self._init_grid_shape()
        self._init_comm()
        self._init_maps()
        self._allocate()
             
    def __del__(self):
        if self.comm is not None:
            self.comm.Free()
             
    def _init_base_comm(self):
        if self.base_comm is None:
            self.base_comm = mpicore.COMM_PRIVATE
        elif isinstance(self.base_comm, MPI.Comm):
            pass
        else:
            raise InvalidBaseCommError("Not an MPI.Comm instance")
        self.comm_size = self.base_comm.Get_size()
        self.comm_rank = self.base_comm.Get_rank()
        
    def _init_grid_shape(self):
        if self.grid_shape is None:
            raise NotImplementedError("grid_shape==None is not supported")
        else:
            # Make it into a tuple
            try:
                self.grid_shape = tuple(self.grid_shape)
            except:
                raise InvalidGridShapeError("grid_shape not castable to a tuple")
            if len(grid_shape)!=self.ndistdim:
                raise InvalidGridShapeError("grid_shape has the wrong length")
            ngriddim = reduce(lambda x,y: x*y, grid_shape)
            if ngriddim != self.comm_size:
                raise InvalidGridShapeError("grid_shape is incompatible with the number of processors")
        
    def _init_comm(self):
        self.comm = self.base_comm.Create_cart(self.grid_shape,
            self.ndistdim*(False,), False)
        self.cart_coords = self.comm.Get_coords(self.comm_rank) 
        
    def _init_maps(self):
        pass
        
    def _parse_dist(self):
        map_class_list = []
        distdims = []
        for k, v in dist.iteritems():
            distdims.append(k)
            map_classes.append(self._to_map_class(v))
        self.distdims = distdims
        self.map_classes = map_classes
        self.ndistdim = len(distdims)
            
    def _to_map_class(self, code):
        if isinstance(code, Map):
            return code
        elif isinstance(code, str):
            lower_code = code.lower()
            if lower_code == 'b':
                return BlockMap
            elif lower_code == 'c':
                return CyclicMap
            elif lower_code == 'bc':
                return BlockCyclicMap
            else:
                raise Exception("Invalid mapping")
        else:
            raise Exception("Invalid mapping")
        
    def _allocate(self):
        self.local_array = np.empty(self.local_shape, dtype=self.dtype)
        

        
    def __getitem__(self, key):
        """Get an item by global indices.
        
        (i,j,k,...) -> (owner, owner), (p,q,k) -> (owner, (p,q,k,...))
        
        """
        owners = numpy.empty(self.ndistdim, dtype=int)
        local_indices = numpy.asaray(key, dtype=int)
        for i in range(self.ndistdim):
            dim = self.distdims[i]
            local_i = key[dim]
            owner, p = self.maps[i].local_i(local_i)
            owners[i] = owner
            local_indices[dim] = p

        print owners
        print local_indices
            
            
        
      
        
 
    
        
    
        


