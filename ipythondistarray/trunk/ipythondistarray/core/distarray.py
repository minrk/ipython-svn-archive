#----------------------------------------------------------------------------
# Imports
#----------------------------------------------------------------------------

from mpi4py import MPI
import numpy as np

from ipythondistarray.mpi import mpibase
from ipythondistarray.core import maps
from ipythondistarray import utils

from ipythondistarray.utils import _raise_nie


#----------------------------------------------------------------------------
# Exceptions
#----------------------------------------------------------------------------

class InvalidBaseCommError(Exception):
    pass

class InvalidGridShapeError(Exception):
    pass

class GridShapeError(Exception):
    pass

class DistError(Exception):
    pass

class DistMatrixError(Exception):
    pass

#----------------------------------------------------------------------------
# Stateless functions for initializing various aspects of DistArray objects
#----------------------------------------------------------------------------

# These are functions rather than methods because they need to be both
# stateless and free of side-effects.  It is possible that they could be
# called multiple times and in multiple different contexts in the course
# of a DistArray object's lifetime (for example upon a reshape or redist).
# The simplest and most robust way of insuring this is to get rid of 'self'
# (which holds all state) and make them standalone functions.

def _init_base_comm(comm):
    if comm==MPI.COMM_NULL:
        raise MPICommError("Cannot create a DistArray with a MPI_COMM_NULL")
    elif comm is None:
        return mpibase.COMM_PRIVATE
    elif isinstance(comm, MPI.Comm):
        return comm
    else:
        raise InvalidBaseCommError("Not an MPI.Comm instance")

def _init_dist(dist, ndim):
    if isinstance(dist, str):
        return ndim*(dist,)
    elif isinstance(dist, (list, tuple)):
        return tuple(dist)
    elif isinstance(dist, dict):
        return tuple([dist.get(i) for i in range(ndim)])
    else:
        DistError("dist must be a string, tuple/list or dict") 

def _init_distdims(dist, ndim):
    reduced_dist = [d for d in dist if d is not None]
    ndistdim = len(reduced_dist)
    if ndistdim > ndim:
        raise DistError("Too many distributed dimensions")
    distdims = [i for i in range(ndim) if dist[i] is not None]
    return tuple(distdims)
    
def _init_map_classes(dist):
    reduced_dist = [d for d in dist if d is not None]
    map_classes = [maps.get_map_class(d) for d in reduced_dist]
    return tuple(map_classes)
             
def _init_grid_shape(shape, grid_shape, distdims, comm_size):
    ndistdim = len(distdims)
    if grid_shape is None:
        grid_shape = _optimize_grid_shape(shape, grid_shape, distdims, comm_size)
    else:
        try:
            grid_shape = tuple(grid_shape)
        except:
            raise InvalidGridShapeError("grid_shape not castable to a tuple")
    if len(grid_shape)!=ndistdim:
        raise InvalidGridShapeError("grid_shape has the wrong length")
    ngriddim = reduce(lambda x,y: x*y, grid_shape)
    if ngriddim != comm_size:
        raise InvalidGridShapeError("grid_shape is incompatible with the number of processors")
    return grid_shape

def _optimize_grid_shape(shape, grid_shape, distdims, comm_size):
    ndistdim = len(distdims)
    if ndistdim==1:
        grid_shape = (comm_size,)
    else:
        factors = utils.mult_partitions(comm_size, ndistdim)
        if factors != []:
            reduced_shape = [shape[i] for i in distdims]
            factors = [utils.mirror_sort(f, reduced_shape) for f in factors]
            rs_ratio = _compute_grid_ratios(reduced_shape)
            f_ratios = [_compute_grid_ratios(f) for f in factors]
            distances = [rs_ratio-f_ratio for f_ratio in f_ratios]
            norms = np.array([np.linalg.norm(d,2) for d in distances])
            index = norms.argmin()
            grid_shape = tuple(factors[index])
        else:
            raise GridShapeError("Cannot distribute array over processors")
    return grid_shape
    
def _compute_grid_ratios(shape):
    n = len(shape)
    return np.array([float(shape[i])/shape[j] for i in range(n) for j in range(n) if i < j])

def _init_comm(base_comm, grid_shape, ndistdim):
    return base_comm.Create_cart(grid_shape,ndistdim*(False,),False)

def _init_local_shape_and_maps(shape, grid_shape, distdims, map_classes):
    maps = []
    local_shape = []
    for i, distdim in enumerate(distdims):
        minst = map_classes[i](shape[distdim], grid_shape[i])
        local_shape.append(minst.local_shape)
        maps.append(minst)
    return tuple(local_shape), tuple(maps)

def local_shape(shape, dist={0:'b'}, grid_shape=None, comm_size=None):
    if comm_size is None:
        raise ValueError("comm_size can't be None")
    ndim = len(shape)
    dist = _init_dist(dist, ndim)
    distdims = _init_distdims(dist, ndim)
    ndistdim = len(distdims)
    map_classes = _init_map_classes(dist)   
    grid_shape = _init_grid_shape(shape, grid_shape, distdims, comm_size)
    local_shape, maps = _init_local_shape_and_maps(shape, 
        grid_shape, distdims, map_classes)
    return local_shape

def grid_shape(shape, dist={0:'b'}, grid_shape=None, comm_size=None):
    if comm_size is None:
        raise ValueError("comm_size can't be None")
    ndim = len(shape)
    dist = _init_dist(dist, ndim)
    distdims = _init_distdims(dist, ndim)
    ndistdim = len(distdims)
    map_classes = _init_map_classes(dist)   
    grid_shape = _init_grid_shape(shape, grid_shape, distdims, comm_size)
    return grid_shape
    
    

#----------------------------------------------------------------------------
# Base DistArray class
#----------------------------------------------------------------------------

class DistArray(object):
    """
    
    Attributes from ndarray:
    
    - flags (no) - not needed
    - shape (yes)
    - strides (yes) - not needed
    - ndim (no)
    - data (yes)
    - size (no)
    - itemsize (no) 
    - nbytes (no)
    - base (no)
    - dtype (yes)
    - real (yes)
    - imag (yes)
    - flat (yes)
    - ctypes (no)
    - __array_interface__ (no)
    - __array_struct_ (no)
    - __array_priority (no)
    """
    
    __array_priority__ = 20.0
    
    def __init__(self, shape, dtype=float, dist={0:'b'} , grid_shape=None,
                 comm=None, buf=None, offset=0):
        """Create a distributed memory array on a set of processors.
        """
        self.shape = shape
        self.ndim = len(shape)
        self.dtype = np.dtype(dtype)
        self.size = reduce(lambda x,y: x*y, shape)
        self.itemsize = self.dtype.itemsize
        self.nbytes = self.size*self.itemsize
        self.data = None
        self.base = None
        self.ctypes = None
                
        # This order is extremely important and is shown by the arguments passed on to
        # subsequent _init_* methods.  It is critical that these _init_* methods are free
        # of side effects and stateless.  This means that they cannot set or get class or
        # instance attributes.  I should probably make them standalone functions.
        self.base_comm = _init_base_comm(comm)
        self.comm_size = self.base_comm.Get_size()
        self.comm_rank = self.base_comm.Get_rank()
            
        self.dist = _init_dist(dist, self.ndim)
        self.distdims = _init_distdims(self.dist, self.ndim)
        self.ndistdim = len(self.distdims)
        self.map_classes = _init_map_classes(self.dist)
                
        self.grid_shape = _init_grid_shape(self.shape, grid_shape, 
            self.distdims, self.comm_size)
        self.comm = _init_comm(self.base_comm, self.grid_shape, self.ndistdim)
        self.cart_coords = self.comm.Get_coords(self.comm_rank)
        self.local_shape, self.maps = _init_local_shape_and_maps(self.shape, 
            self.grid_shape, self.distdims, self.map_classes)
        self.local_size = reduce(lambda x,y: x*y, self.local_shape)
        
        # At this point, everything is setup, but the memory has not been allocated.
        self._allocate(buf, offset)
             
    def __del__(self):
        if self.comm is not None:
            self.comm.Free()
             
    #----------------------------------------------------------------------------
    # Methods used at initialization
    #----------------------------------------------------------------------------   
            
    def _allocate(self, buf=None, offset=0):
        if buf is None:
            # Allocate a new array and use its data attribute as my own
            self.local_array = np.empty(self.local_shape, dtype=self.dtype)
            self.data = self.local_array.data
        else:
            try:
                buf = buffer(buf)
            except TypeError:
                raise TypeError("the object is not or can't be made into a buffer")
            try:
                self.local_array = np.frombuffer(buf, dtype=self.dtype, count=self.local_size, offset=offset)
                self.local_array.shape = self.local_shape
                self.data = self.local_array.data
            except ValueError:
                raise ValueError("the buffer is smaller than needed for this array")
            
    #----------------------------------------------------------------------------
    # Methods related to distributed indexing
    #----------------------------------------------------------------------------   
        
    def get_localarray(self):
        return self.local_view()
        
    def set_localarray(self, a):
        a = np.asarray(a, dtype=self.dtype, order='C')
        if a.shape != self.local_shape:
            raise ValueError("incompatible local array shape")
        b = buffer(a)
        self.local_array = np.frombuffer(b,dtype=self.dtype)
        self.local_array.shape = self.local_shape
        
    def owner_rank(self, *indices):
        owners = [self.maps[i].owner(indices[self.distdims[i]]) for i in range(self.ndistdim)]
        return self.comm.Get_cart_rank(owners)
        
    def owner_coords(self, *indices):
        owners = [self.maps[i].owner(indices[self.distdims[i]]) for i in range(self.ndistdim)]
        return owners          
    
    def rank_to_coords(self, rank):
        return self.comm.Get_coords(rank)
    
    def coords_to_rank(self, coords):
        return self.comm.Get_cart_rank(coords)
        
    def local_ind(self, *global_ind):
        local_ind = list(global_ind)
        for i in range(self.ndistdim):
            dd = self.distdims[i]
            local_ind[dd] = self.maps[i].local_index(global_ind[dd])
        return tuple(local_ind)

    def global_ind(self, owner, *local_ind):
        if isinstance(owner, int):
            owner_coords = self.rank_to_coords(owner)
        else:
            owner_coords = owner
        global_ind = list(local_ind)
        for i in range(self.ndistdim):
            dd = self.distdims[i]
            global_ind[dd] = self.maps[i].global_index(owner_coords[i], local_ind[dd])
        return tuple(global_ind)
        
    def get_dist_matrix(self):
        if self.ndim==2:
            a = np.empty(self.shape,dtype=int)
            for i in range(self.shape[0]):
                for j in range(self.shape[1]):
                    a[i,j] = self.owner_rank(i,j)
            return a
        else:
            raise DistMatrixError("The dist matrix can only be created for a 2d array")        

    #----------------------------------------------------------------------------
    # 3.2 ndarray methods
    #----------------------------------------------------------------------------   

    #----------------------------------------------------------------------------
    # 3.2.1 Array conversion
    #---------------------------------------------------------------------------- 
        
    def astype(self, dtype):
        if dtype is None:
            return self.copy()
        else:
            local_copy = self.local_array.astype(dtype)
            new_da = DistArray(self.shape, dtype=self.dtype, dist=self.dist,
                grid_shape=self.grid_shape, comm=self.base_comm, buf=local_copy)
            return new_da
                            
    def copy(self):
        local_copy = self.local_array.copy()
        new_da = DistArray(self.shape, dtype=self.dtype, dist=self.dist,
            grid_shape=self.grid_shape, comm=self.base_comm, buf=local_copy)
        
    def local_view(self, dtype=None):
        return self.local_array.view(dtype)
        
    def view(self, dtype=None):
        new_da = DistArray(self.shape, self.dtype, self.dist,
            self.grid_shape, self.base_comm, buf=self.data)
        return new_da
        
    def __distarray__(dtype=None):
        return self
        
    def fill(self, scalar):
        self.local_array.fill(scalar)

    #----------------------------------------------------------------------------
    # 3.2.2 Array shape manipulation
    #---------------------------------------------------------------------------- 

    def reshape(self, newshape):
        _raise_nie()
        
    def resize(self, newshape, refcheck=1, order='C'):
        _raise_nie()
        
    def transpose(self, arg):
        _raise_nie()
        
    def swapaxes(self, axis1, axis2):
        _raise_nie()
        
    def flatten(self, order='C'):
        _raise_nie()
        
    def ravel(self, order='C'):
        _raise_nie()
    
    def squeeze(self):
        _raise_nie()
     
    def asdist(self, shape, dist={0:'b'}, grid_shape=None):
        new_da = DistArray(shape, self.dtype, dist, grid_shape, self.base_comm)
        base_comm = self.base_comm
        local_array = self.local_array
        new_local_array = da.local_array
        recv_counts = np.zeros(self.comm_size, dtype=int)

        status = MPI.Status()
        MPI.Attach_buffer(np.empty(128+MPI.BSEND_OVERHEAD,dtype=float))
        done_count = 0
        
        for old_local_inds, item in np.ndenumerate(local_array):

            # Compute the new owner
            global_inds = self.global_ind(new_da.comm_rank, old_local_inds)
            new_owner = new_da.owner_rank(global_inds)
            if new_owner==self.owner_rank:
                pass
                # Just move the data to the right place in new_local_array
            else:
                # Send to the new owner with default tag
                # Bsend is probably best, but Isend is also a possibility.
                request = comm.Isend(item, dest=new_owner)

            # Recv
            incoming = comm.Iprobe(MPI.ANY_SOURCE, MPI.ANY_TAG, status)
            if incoming:
                old_owner = status.Get_source()
                tag = status.Get_tag()
                data = comm.Recv(old_owner, tag)
                if tag==2:
                    done_count += 1
                # Figure out where new location of old_owner, tag
                new_local_ind = local_ind_by_owner_and_location(old_owner, location)
                new_local_array[new_local_ind] = y
                recv_counts[old_owner] = recv_counts[old_owner]+1
        
        while done_count < self.comm_size:
            pass
            
        
        MPI.Detach_buffer()
            
     
     
    #----------------------------------------------------------------------------
    # 3.2.3 Array item selection and manipulation
    #----------------------------------------------------------------------------   
    
    def take(self, indices, axis=None, out=None, mode='raise'):
        _raise_nie()
        
    def put(self, values, indices, mode='raise'):
        _raise_nie()
        
    def putmask(self, values, mask):
        _raise_nie()
            
    def repeat(self, repeats, axis=None):
        _raise_nie()
                
    def choose(self, choices, out=None, mode='raise'):
        _raise_nie()
                
    def sort(self, axis=-1, kind='quick'):
        _raise_nie()
                
    def argsort(self, axis=-1, kind='quick'):
        _raise_nie()
                
    def searchsorted(self, values):
        _raise_nie()

    def nonzero(self):
        _raise_nie()
                
    def compress(self, condition, axis=None, out=None):
        _raise_nie()
                
    def diagonal(self, offset=0, axis1=0, axis2=1):
        _raise_nie()
            
    #----------------------------------------------------------------------------
    # 3.2.4 Array item selection and manipulation
    #---------------------------------------------------------------------------- 
    
    def max(self, axis=None, out=None):
        _raise_nie()
                
    def argmax(self, axis=None, out=None):
        _raise_nie()
                
    def min(axis=None, out=None):
        _raise_nie()
                
    def argmin(self, axis=None, out=None):
        _raise_nie()
        
    def ptp(self, axis=None, out=None):
        _raise_nie()
                
    def clip(self, min, max, out=None):
        _raise_nie()
            
    def conj(self, out=None):
        _raise_nie()
                
    congugate = conj
    
    def round(self, decimals=0, out=None):
        _raise_nie()
                
    def trace(self, offset=0, axis1=0, axis2=1, dtype=None, out=None):
        _raise_nie()
                
    def sum(self, axis=None, dtype=None, out=None):
        _raise_nie()
        
    def cumsum(self, axis=None, dtype=None, out=None):        
        _raise_nie()
        
    def mean(self, axis=None, dtype=None, out=None):
        _raise_nie()
        
    def var(self, axis=None, dtype=None, out=None):
        _raise_nie()
          
    def std(self, axis=None, dtype=None, out=None):
        _raise_nie()
        
    def prod(self, axis=None, dtype=None, out=None):
        _raise_nie()
        
    def cumprod(self, axis=None, dtype=None, out=None):
        _raise_nie()
        
    def all(self, axis=None, out=None):
        _raise_nie()
        
    def any(self, axis=None, out=None):    
        _raise_nie()

    #----------------------------------------------------------------------------
    # 3.3 Array special methods
    #---------------------------------------------------------------------------- 

    #----------------------------------------------------------------------------
    # 3.3.1 Methods for standard library functions
    #----------------------------------------------------------------------------

    def __copy__(self):
        _raise_nie()
            
    def __deepcopy__(self):
        _raise_nie()
        
    #----------------------------------------------------------------------------
    # 3.3.2 Basic customization
    #----------------------------------------------------------------------------
        
    def __lt__(self, other):
        _raise_nie()
        
    def __le__(self, other):
        _raise_nie()
        
    def __gt__(self, other):
        _raise_nie()
        
    def __ge__(self, other):
        _raise_nie()
        
    def __eq__(self, other):
        _raise_nie()
        
    def __ne__(self, other):
        _raise_nie()
        
    def __str__(self):
        _raise_nie()
        
    def __repr__(self):
        _raise_nie()
        
    def __nonzero__(self):
        _raise_nie()
        
    #----------------------------------------------------------------------------
    # 3.3.3 Container customization
    #----------------------------------------------------------------------------    
    
    def __len__(self):
        return self.shape[0]
    
    def __getitem__(self, key):
        _raise_nie()
        
    def __setitem__(self, key, value):
        _raise_nie()
        
    def __contains__(self, item):
        _raise_nie()
        
    #----------------------------------------------------------------------------
    # 3.3.4 Arithmetic customization - binary
    #---------------------------------------------------------------------------- 

    # Binary

    def __add__(self, other):
        _raise_nie()
        
    def __sub__(self, other):
        _raise_nie()
        
    def __mul__(self, other):
        _raise_nie()
        
    def __div__(self, other):
        _raise_nie()
        
    def __truediv__(self, other):
        _raise_nie()
        
    def __floordiv__(self, other):
        _raise_nie()
        
    def __mod__(self, other):
        _raise_nie()
        
    def __divmod__(self, other):
        _raise_nie()
        
    def __pow__(self, other, modulo=None):
        _raise_nie()
        
    def __lshift__(self, other):
        _raise_nie()
        
    def __rshift__(self, other):
        _raise_nie()
        
    def __and__(self, other):
        _raise_nie()
        
    def __or__(self, other):
        _raise_nie()
        
    def __xor__(self, other):
        _raise_nie()

    # Binary - right versions

    def __radd__(self, other):
        _raise_nie()
        
    def __rsub__(self, other):
        _raise_nie()
        
    def __rmul__(self, other):
        _raise_nie()
        
    def __rdiv__(self, other):
        _raise_nie()
        
    def __rtruediv__(self, other):
        _raise_nie()
        
    def __rfloordiv__(self, other):
        _raise_nie()
        
    def __rmod__(self, other):
        _raise_nie()
        
    def __rdivmod__(self, other):
        _raise_nie()
        
    def __rpow__(self, other, modulo=None):
        _raise_nie()
        
    def __rlshift__(self, other):
        _raise_nie()
        
    def __rrshift__(self, other):
        _raise_nie()
        
    def __rand__(self, other):
        _raise_nie()
        
    def __ror__(self, other):
        _raise_nie()
        
    def __rxor__(self, other):
        _raise_nie()
        
    # Inplace
    
    def __iadd__(self, other):
        _raise_nie()
        
    def __isub__(self, other):
        _raise_nie()
        
    def __imul__(self, other):
        _raise_nie()
        
    def __idiv__(self, other):
        _raise_nie()
        
    def __itruediv__(self, other):
        _raise_nie()
        
    def __ifloordiv__(self, other):
        _raise_nie()
        
    def __imod__(self, other):
        _raise_nie()
                
    def __ipow__(self, other, modulo=None):
        _raise_nie()
        
    def __ilshift__(self, other):
        _raise_nie()
        
    def __irshift__(self, other):
        _raise_nie()
        
    def __iand__(self, other):
        _raise_nie()
        
    def __ior__(self, other):
        _raise_nie()
        
    def __ixor__(self, other):
        _raise_nie()
        
    # Unary
    
    def __neg__(self):
        _raise_nie()
        
    def __pos__(self):
        _raise_nie()
        
    def __abs__(self):
        _raise_nie()
    
    def __invert__(self):
        _raise_nie()
        

        


