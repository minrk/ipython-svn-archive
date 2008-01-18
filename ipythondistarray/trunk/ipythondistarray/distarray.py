import numpy as np

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


class ProcessorGrid(object):
        
    def __init__(self, shape):
        self.shape = shape
        self.nprocessors = None
        self.ndim = len(shape)
        self._calc_proc_strides()
        
    def rank_from_indices(*args):
        rank = None

class DistArray(object):
    
    def __init__(self, shape, dist={0:'b'}, dtype=float, proc_grid=None):
        """Create a distributed memory array.
        
        dist = {0:'b',2:'c',3:'bc'}
        """
        self.ndim = len(shape)
        self.shape = shape
        self.dtype = np.dtype(dtype)
        self._parse_dist(dist)
        self._create_proc_grid(proc_grid)
        self._create_maps()
        
    def _parse_dist(self, dist):
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
        
    def _create_proc_grid(self, proc_grid):
        """Create a processor grid"""
        self.proc_grid = None
        
    def _create_maps(self):
        """Create a list of map instances.
        
        These can be used to 
        """
        
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
            
            
        
      
        
 
    
        
    
        


