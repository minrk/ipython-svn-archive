#----------------------------------------------------------------------------
# Imports
#----------------------------------------------------------------------------


from mpi4py import MPI
import numpy as np

from ipythondistarray.core.base import BaseDistArray, arecompatible
from ipythondistarray.core.error import *
from ipythondistarray.core.construct import (
    init_base_comm,
    init_dist,
    init_distdims,
    init_map_classes,
    init_grid_shape,
    optimize_grid_shape,
    init_comm,
    init_local_shape_and_maps,
    find_local_shape,
    find_grid_shape)


#----------------------------------------------------------------------------
# Exports
#----------------------------------------------------------------------------


__all__ = [
    'NullDistArray',
    'null_like',
    'isnull',
    'anynull',
    'nonenull',
    'allnull']


#----------------------------------------------------------------------------
# The NullDistArray things
#----------------------------------------------------------------------------


class NullDistArray(BaseDistArray):
    """
    A null DistArray for COMM_NULL communicators.
    
    All attribute access should raise NullArrayAttributeError, except for base
    and base_comm, which should return COMM_NULL.  Attributes (shape, dist, etc.)
    that are set in __init__ are saved with single underscores.  This is because
    these attributes are useful internally, but shouldn't be available to users.
    
    Methods that return None or a DistArray should return None or a NullDistArray.
    This behavior is mostly implemented, but I still haven't gone through all the
    methods yet.
    """
    
    __array_priority__ = 20.0
    
    
    def __init__(self, shape=None, dtype=float, dist={0:'b'} , grid_shape=None,
                 comm=None, buf=None, offset=0):
        """Create a distributed memory array on a set of processors.
        """
        
        self._setit('_shape', shape)
        self._setit('_ndim', len(shape))
        self._setit('_dtype', np.dtype(dtype))
        self._setit('_size', reduce(lambda x,y: x*y, shape))
        self._setit('_itemsize', self._dtype.itemsize)
        self._setit('_nbytes', self._size*self._itemsize)
                
        if comm==MPI.COMM_NULL or comm is None:
            object.__setattr__(self, 'base_comm', MPI.COMM_NULL)
            object.__setattr__(self, 'comm', MPI.COMM_NULL)
        else:
            raise InvalidBaseCommError("a NullDistArray can only be created with MPI.COMM_NULL")
    
        self._setit('_dist', init_dist(dist, self._ndim))
        self._setit('_distdims', init_distdims(self._dist, self._ndim))
        self._setit('_ndistdim', len(self._distdims))
        
        self._setit('_grid_shape', grid_shape)
    
    def _setit(self, name, value):
        object.__setattr__(self, name, value)
    
    #----------------------------------------------------------------------------
    # Methods related to this classes null nature
    #----------------------------------------------------------------------------   
    
    def _raise_null_array(self):
        raise NullArrayError("cannot perform operation on null array")
    
    def isnull(self):
        return True
    
    def __getattr__(self, name): 
        raise NullArrayAttributeError("cannot get attribute on NullDistArray: %s" % name)
    
    def __setattr__(self, name, value):
        raise NullArrayAttributeError("cannot set attribute on NullDistArray: %s" % name)
    
    def __delattr__(self, name):
        raise NullArrayAttributeError("cannot del attribute on NullDistArray: %s" % name)
    
    def compatibility_hash(self):
        return hash((self._shape, self._dist, self._grid_shape, True))
        
    
    #----------------------------------------------------------------------------
    # Methods related to distributed indexing
    #----------------------------------------------------------------------------   
    
    def get_localarray(self):
        self._raise_null_array()
    
    def set_localarray(self, a):
        return None
    
    def owner_rank(self, *indices):
        self._raise_null_array()
    
    def owner_coords(self, *indices):
        self._raise_null_array()          
    
    def rank_to_coords(self, rank):
        self._raise_null_array()
    
    def coords_to_rank(self, coords):
        self._raise_null_array()
    
    def local_ind(self, *global_ind):
        self._raise_null_array()
    
    def global_ind(self, owner, *local_ind):
        self._raise_null_array()
    
    def get_dist_matrix(self):
        self._raise_null_array()        
    
    #----------------------------------------------------------------------------
    # 3.2 ndarray methods
    #----------------------------------------------------------------------------   
    
    #----------------------------------------------------------------------------
    # 3.2.1 Array conversion
    #---------------------------------------------------------------------------- 
    
    def astype(self, dtype):
        return null_like(self)
    
    def copy(self):
        return null_like(self)
    
    def local_view(self, dtype=None):
        self._raise_null_array()
    
    def view(self, dtype=None):
        self._raise_null_array()
    
    def __distarray__(dtype=None):
        return self
    
    def fill(self, scalar):
        return None
    
    #----------------------------------------------------------------------------
    # 3.2.2 Array shape manipulation
    #---------------------------------------------------------------------------- 
    
    def reshape(self, newshape):
        return null_like(self)
    
    def redist(self, newshape, newdist={0:'b'}, newgrid_shape=None):
        return None
    
    def resize(self, newshape, refcheck=1, order='C'):
        return None
    
    def transpose(self, arg):
        return null_like(self)
    
    def swapaxes(self, axis1, axis2):
        return self
    
    def flatten(self, order='C'):
        return null_like(self)
    
    def ravel(self, order='C'):
        return self
    
    def squeeze(self):
        return self
     
    def asdist(self, shape, dist={0:'b'}, grid_shape=None):
        return self
    
    def asdist_like(self, other):
        """
        Return a version of self that has shape, dist and grid_shape like other.
        """
        if arecompatible(self, other):
            return self
        else:
            raise IncompatibleArrayError("DistArrays have incompatible shape, dist or grid_shape")

    
    #----------------------------------------------------------------------------
    # 3.2.3 Array item selection and manipulation
    #----------------------------------------------------------------------------   
    
    def take(self, indices, axis=None, out=None, mode='raise'):
        return null_like(self)
    
    def put(self, values, indices, mode='raise'):
        return None
    
    def putmask(self, values, mask):
        return None
    
    def repeat(self, repeats, axis=None):
        return None
    
    def choose(self, choices, out=None, mode='raise'):
        return null_like(self)
    
    def sort(self, axis=-1, kind='quick'):
        return None
    
    def argsort(self, axis=-1, kind='quick'):
        self._raise_null_array()
    
    def searchsorted(self, values):
        self._raise_null_array()
    
    def nonzero(self):
        self._raise_null_array()
    
    def compress(self, condition, axis=None, out=None):
        self._raise_null_array()
    
    def diagonal(self, offset=0, axis1=0, axis2=1):
        return null_like(self)
    
    #----------------------------------------------------------------------------
    # 3.2.4 Array item selection and manipulation
    #---------------------------------------------------------------------------- 
    
    def max(self, axis=None, out=None):
        self._raise_null_array()
    
    def argmax(self, axis=None, out=None):
        self._raise_null_array()
    
    def min(axis=None, out=None):
        self._raise_null_array()
    
    def argmin(self, axis=None, out=None):
        self._raise_null_array()
    
    def ptp(self, axis=None, out=None):
        self._raise_null_array()
    
    def clip(self, min, max, out=None):
        self._raise_null_array()
    
    def conj(self, out=None):
        self._raise_null_array()
    
    congugate = conj
    
    def round(self, decimals=0, out=None):
        self._raise_null_array()
    
    def trace(self, offset=0, axis1=0, axis2=1, dtype=None, out=None):
        self._raise_null_array()
    
    def sum(self, axis=None, dtype=None, out=None):
        self._raise_null_array()
    
    def cumsum(self, axis=None, dtype=None, out=None):        
        self._raise_null_array()
    
    def mean(self, axis=None, dtype=None, out=None):
        self._raise_null_array()
    
    def var(self, axis=None, dtype=None, out=None):
        self._raise_null_array()
     
    def std(self, axis=None, dtype=None, out=None):
        self._raise_null_array()
    
    def prod(self, axis=None, dtype=None, out=None):
        self._raise_null_array()
    
    def cumprod(self, axis=None, dtype=None, out=None):
        self._raise_null_array()
    
    def all(self, axis=None, out=None):
        self._raise_null_array()
    
    def any(self, axis=None, out=None):    
        self._raise_null_array()
    
    #----------------------------------------------------------------------------
    # 3.3 Array special methods
    #---------------------------------------------------------------------------- 
    
    #----------------------------------------------------------------------------
    # 3.3.1 Methods for standard library functions
    #----------------------------------------------------------------------------
    
    def __copy__(self):
        self._raise_null_array()
    
    def __deepcopy__(self):
        self._raise_null_array()
    
    #----------------------------------------------------------------------------
    # 3.3.2 Basic customization
    #----------------------------------------------------------------------------
    
    def __lt__(self, other):
        self._raise_null_array()
    
    def __le__(self, other):
        self._raise_null_array()
    
    def __gt__(self, other):
        self._raise_null_array()
    
    def __ge__(self, other):
        self._raise_null_array()
    
    def __eq__(self, other):
        self._raise_null_array()
    
    def __ne__(self, other):
        self._raise_null_array()
    
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return "<%s at %s>" % (self.__class__.__name__, hex(id(self)))
    
    def __nonzero__(self):
        self._raise_null_array()
    
    #----------------------------------------------------------------------------
    # 3.3.3 Container customization
    #----------------------------------------------------------------------------    
    
    def __len__(self):
        return self.shape[0]
    
    def __getitem__(self, key):
        self._raise_null_array()
    
    def __setitem__(self, key, value):
        self._raise_null_array()
    
    def __contains__(self, item):
        self._raise_null_array()
    
    #----------------------------------------------------------------------------
    # 3.3.4 Arithmetic customization - binary
    #---------------------------------------------------------------------------- 
    
    # Binary
    
    def __add__(self, other):
        self._raise_null_array()
    
    def __sub__(self, other):
        self._raise_null_array()
    
    def __mul__(self, other):
        self._raise_null_array()
    
    def __div__(self, other):
        self._raise_null_array()
    
    def __truediv__(self, other):
        self._raise_null_array()
    
    def __floordiv__(self, other):
        self._raise_null_array()
    
    def __mod__(self, other):
        self._raise_null_array()
    
    def __divmod__(self, other):
        self._raise_null_array()
    
    def __pow__(self, other, modulo=None):
        self._raise_null_array()
    
    def __lshift__(self, other):
        self._raise_null_array()
    
    def __rshift__(self, other):
        self._raise_null_array()
    
    def __and__(self, other):
        self._raise_null_array()
    
    def __or__(self, other):
        self._raise_null_array()
    
    def __xor__(self, other):
        self._raise_null_array()
        
    # Binary - right versions
    
    def __radd__(self, other):
        self._raise_null_array()
    
    def __rsub__(self, other):
        self._raise_null_array()
    
    def __rmul__(self, other):
        self._raise_null_array()
    
    def __rdiv__(self, other):
        self._raise_null_array()
    
    def __rtruediv__(self, other):
        self._raise_null_array()
    
    def __rfloordiv__(self, other):
        self._raise_null_array()
    
    def __rmod__(self, other):
        self._raise_null_array()
    
    def __rdivmod__(self, other):
        self._raise_null_array()
    
    def __rpow__(self, other, modulo=None):
        self._raise_null_array()
    
    def __rlshift__(self, other):
        self._raise_null_array()
    
    def __rrshift__(self, other):
        self._raise_null_array()
    
    def __rand__(self, other):
        self._raise_null_array()
    
    def __ror__(self, other):
        self._raise_null_array()
    
    def __rxor__(self, other):
        self._raise_null_array()
    
    # Inplace
    
    def __iadd__(self, other):
        self._raise_null_array()
    
    def __isub__(self, other):
        self._raise_null_array()
    
    def __imul__(self, other):
        self._raise_null_array()
    
    def __idiv__(self, other):
        self._raise_null_array()
    
    def __itruediv__(self, other):
        self._raise_null_array()
    
    def __ifloordiv__(self, other):
        self._raise_null_array()
    
    def __imod__(self, other):
        self._raise_null_array()
    
    def __ipow__(self, other, modulo=None):
        self._raise_null_array()
    
    def __ilshift__(self, other):
        self._raise_null_array()
    
    def __irshift__(self, other):
        self._raise_null_array()
    
    def __iand__(self, other):
        self._raise_null_array()
    
    def __ior__(self, other):
        self._raise_null_array()
    
    def __ixor__(self, other):
        self._raise_null_array()
    
    # Unary
    
    def __neg__(self):
        self._raise_null_array()
    
    def __pos__(self):
        self._raise_null_array()
    
    def __abs__(self):
        self._raise_null_array()
    
    def __invert__(self):
        self._raise_null_array()


def null_like(a):
    return NullDistArray(shape=a._shape, dtype=a._dtype, dist=a._dist, 
        grid_shape=a._grid_shape, comm=a.base_comm)


def isnull(a):
    return a.isnull()


def allnull(*args):
    result = True
    for arr in args:
        if not arr.isnull():
            result = False
    return result


def anynull(*args):
    result = False
    for arr in args:
        if arr.isnull():
            result = True
    return result


def nonenull(*args):
    result = True
    for arr in args:
        if arr.isnull():
            result = False
    return result

