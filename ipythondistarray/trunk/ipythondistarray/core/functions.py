#----------------------------------------------------------------------------
# Imports
#----------------------------------------------------------------------------

import numpy as np

from ipythondistarray.core import distarray
from ipythondistarray.core.distarray import DistArray
from ipythondistarray.utils import _raise_nie


#----------------------------------------------------------------------------
# Utilities needed to implement things below
#----------------------------------------------------------------------------




#----------------------------------------------------------------------------
# 4 Basic routines 
#----------------------------------------------------------------------------

#----------------------------------------------------------------------------
# 4.1 Creating arrays 
#----------------------------------------------------------------------------

# Here is DistArray.__init__ for reference
# def __init__(self, shape, dtype=float, dist={0:'b'} , grid_shape=None,
#              comm=None, buf=None, offset=0):

def distarray(object, dtype=None, copy=True, order=None, subok=False, ndmin=0):
    _raise_nie()
    
def asdistarray(object, dtype=None, order=None):
    _raise_nie()
    
def arange(start, stop=None, step=1, dtype=None, dist={0:'b'}, 
    grid_shape=None, comm=None):
    _raise_nie()
    

def empty(shape, dtype=int, dist={0:'b'}, grid_shape=None, comm=None):
    return DistArray(shape, dtype, dist, grid_shape, comm)

def empty_like(arr):
    if not isinstance(arr, DistArray):
        raise TypeError("a DistArray or subclass is expected")
    return empty(arr.shape, arr.dtype, arr.dist, arr.grid_shape, arr.base_comm)
    
def zeros(shape, dtype=int, dist={0:'b'}, grid_shape=None, comm=None):
    local_shape = distarray.local_shape(shape, dist, grid_shape, comm.Get_size())
    local_zeros = np.zeros(local_shape, dtype=dtype)
    return DistArray(shape, dtype, dist, grid_shape, comm, buf=local_zeros)

def zeros_like(arr):
    if not isinstance(arr, DistArray):
        raise TypeError("a DistArray or subclass is expected")
    return zeros(arr.shape, arr.dtype, arr.dist, arr.grid_shape, arr.base_comm)
    
def ones(shape, dtype=int, dist={0:'b'}, grid_shape=None, comm=None):
    local_shape = distarray.local_shape(shape, dist, grid_shape, comm.Get_size())
    local_ones = np.ones(local_shape, dtype=dtype)
    return DistArray(shape, dtype, dist, grid_shape, comm, buf=local_ones)

def fromfunction(function, **kwargs):
    dtype = kwargs.pop('dtype', int)
    dist = kwargs.pop('dist', {0:'b'})
    grid_shape = kwargs.pop('grid_shape', None)
    comm = kwargs.pop('comm', None)
    da = empty(shape, dtype, dist, grid_shape, comm)
    local_view = da.local_view()
    for local_inds, x in np.ndenumerate(local_view):
        global_inds = da.global_inds(*local_inds)
        local_view[local_inds] = function(*global_inds, **kwargs)
    
def identity(n, dtype=np.intp):
    _raise_nie()

def where(condition, x=None, y=None):
    _raise_nie()


#----------------------------------------------------------------------------
# 4.2 Operations on two or more arrays 
#----------------------------------------------------------------------------

def concatenate(seq, axis=0):
    _raise_nie()

def correlate(x, y, mode='valid'):
    _raise_nie()

def convolve(x, y, mode='valid'):
    _raise_nie()

def outer(a, b):
    _raise_nie()

def inner(a, b):
    _raise_nie()

def dot(a, b):
    _raise_nie()

def vdot(a, b):
    _raise_nie()

def tensordot(a, b, axes=(-1,0)):
    _raise_nie()

def cross(a, b, axisa=-1, axisb=-1, axisc=-1, axis=None):
    _raise_nie()

def allclose(a, b, rtol=10e-5, atom=10e-8):
    _raise_nie()


#----------------------------------------------------------------------------
# 4.3 Printing arrays 
#----------------------------------------------------------------------------

def distarray2string(a):
    _raise_nie()

def set_printoptions(precision=None, threshold=None, edgeitems=None, 
                     linewidth=None, suppress=None):
    return np.set_printoptions(precision, threshold, edgeitems, linewidth, suppress)

def get_printoptions():
    return np.get_printoptions()


#----------------------------------------------------------------------------
# 4.5 Dealing with data types
#----------------------------------------------------------------------------  

dtype = np.dtype
maximum_sctype = np.maximum_sctype
issctype = np.issctype
obj2sctype = np.obj2sctype
sctype2char = np.sctype2char
can_cast = np.can_cast


#----------------------------------------------------------------------------
# 5 Additional convenience routines
#----------------------------------------------------------------------------


#----------------------------------------------------------------------------
# 5.1 Shape functions
#----------------------------------------------------------------------------


#----------------------------------------------------------------------------
# 5.2 Basic functions
#----------------------------------------------------------------------------

def average(a, axis=None, weights=None, returned=0):
    _raise_nie()
    
def cov(x, y=None, rowvar=1, bias=0):
    _raise_nie()
    
def corrcoef(x, y=None, rowvar=1, bias=0):
    _raise_nie()

def median(m):
    _raise_nie()

def digitize(x, bins):
    _raise_nie()

def histogram(x, bins=None, range=None, normed=False):
    _raise_nie()

def histogram2d(x, y, bins, normed=False):
    _raise_nie()

def logspace(start, stop, num=50, endpoint=True, base=10.0):
    _raise_nie()

def linspace(start, stop, num=50, endpoint=True, retstep=False):
    _raise_nie()



#----------------------------------------------------------------------------
# 5.3 Polynomial functions
#----------------------------------------------------------------------------


#----------------------------------------------------------------------------
# 5.4 Set operations
#----------------------------------------------------------------------------


#----------------------------------------------------------------------------
# 5.5 Array construction using index tricks
#----------------------------------------------------------------------------


#----------------------------------------------------------------------------
# 5.6 Other indexing devices
#----------------------------------------------------------------------------


#----------------------------------------------------------------------------
# 5.7 Two-dimensional functions
#----------------------------------------------------------------------------

def eye(n, m=None, k=0, dtype=float):
    _raise_nie()

def diag(v, k=0):
    _raise_nie()

#----------------------------------------------------------------------------
# 5.8 More data type functions
#----------------------------------------------------------------------------

issubclass_ = np.issubclass_
issubdtype = np.issubdtype
iscomplexobj = np.iscomplexobj
isrealobj = np.isrealobj
isscalar = np.isscalar
nan_to_num = np.nan_to_num
real_if_close = np.real_if_close
cast = np.cast
mintypecode = np.mintypecode
finfo = np.finfo



#----------------------------------------------------------------------------
# 5.9 Functions that behave like ufuncs
#----------------------------------------------------------------------------


#----------------------------------------------------------------------------
# 5.10 Misc functions
#----------------------------------------------------------------------------


#----------------------------------------------------------------------------
# 5.11 Utility functions
#----------------------------------------------------------------------------

