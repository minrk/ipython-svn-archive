from mpi4py import MPI
import numpy as np

from ipythondistarray.core.error import *


__all__ = [
    'NullDistArray',
    'null_like',
    'isnull']

class NullDistArray(object):
    """
    A null DistArray for COMM_NULL communicators.
    """
    
    __array_priority__ = 20.0
    
    
    def __init__(self, shape, dtype=float, dist={0:'b'} , grid_shape=None,
                 comm=None, buf=None, offset=0):
        """Create a distributed memory array on a set of processors.
        """
        object.__setattr__(self, 'shape', shape)
        object.__setattr__(self, 'ndim', len(shape))
        object.__setattr__(self, 'dtype', np.dtype(dtype))
        object.__setattr__(self, 'size', reduce(lambda x,y: x*y, shape))
        object.__setattr__(self, 'itemsize', self.dtype.itemsize)
        object.__setattr__(self, 'nbytes', self.size*self.itemsize)
        
        if comm==MPI.COMM_NULL:
            object.__setattr__(self, 'base_comm', comm)
        elif comm is None:
            object.__setattr__(self, 'base_comm', MPI.COMM_NULL)
        else:
            InvalidBaseCommError("a NullDistArray can only be created with MPI.COMM_NULL")
        
        object.__setattr__(self, 'comm_size', 0)
        object.__setattr__(self, 'comm_rank', 0)
        object.__setattr__(self, 'comm', self.base_comm)
    
    
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
    
    #----------------------------------------------------------------------------
    # Methods related to distributed indexing
    #----------------------------------------------------------------------------   
    
    def get_localarray(self):
        self._raise_null_array()
    
    def set_localarray(self, a):
        self._raise_null_array()
    
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
        self._raise_null_array()
    
    def copy(self):
        self._raise_null_array()
    
    def local_view(self, dtype=None):
        self._raise_null_array()
    
    def view(self, dtype=None):
        self._raise_null_array()
    
    def __distarray__(dtype=None):
        self._raise_null_array()
    
    def fill(self, scalar):
        self._raise_null_array()
    
    #----------------------------------------------------------------------------
    # 3.2.2 Array shape manipulation
    #---------------------------------------------------------------------------- 
    
    def reshape(self, newshape):
        self._raise_null_array()
    
    def redist(self, newshape, newdist={0:'b'}, newgrid_shape=None):
        self._raise_null_array()
    
    def resize(self, newshape, refcheck=1, order='C'):
        self._raise_null_array()
    
    def transpose(self, arg):
        self._raise_null_array()
    
    def swapaxes(self, axis1, axis2):
        self._raise_null_array()
    
    def flatten(self, order='C'):
        self._raise_null_array()
    
    def ravel(self, order='C'):
        self._raise_null_array()
    
    def squeeze(self):
        self._raise_null_array()
     
    def asdist(self, shape, dist={0:'b'}, grid_shape=None):
        self._raise_null_array()
    
    def asdist_like(self, other):
        self._raise_null_array()
    
    #----------------------------------------------------------------------------
    # 3.2.3 Array item selection and manipulation
    #----------------------------------------------------------------------------   
    
    def take(self, indices, axis=None, out=None, mode='raise'):
        self._raise_null_array()
    
    def put(self, values, indices, mode='raise'):
        self._raise_null_array()
    
    def putmask(self, values, mask):
        self._raise_null_array()
    
    def repeat(self, repeats, axis=None):
        self._raise_null_array()
    
    def choose(self, choices, out=None, mode='raise'):
        self._raise_null_array()
    
    def sort(self, axis=-1, kind='quick'):
        self._raise_null_array()
    
    def argsort(self, axis=-1, kind='quick'):
        self._raise_null_array()
    
    def searchsorted(self, values):
        self._raise_null_array()
    
    def nonzero(self):
        self._raise_null_array()
    
    def compress(self, condition, axis=None, out=None):
        self._raise_null_array()
    
    def diagonal(self, offset=0, axis1=0, axis2=1):
        self._raise_null_array()
    
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
        self._raise_null_array()
    
    def __repr__(self):
        self._raise_null_array()
    
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
    return NullDistArray(a.shape, a.dtype, comm=a.base_comm)


def isnull(a):
    return a.isnull()
