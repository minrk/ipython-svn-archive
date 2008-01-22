include "include/mpi.pxi"

cdef public class Comm:
        
    cdef MPI_Comm comm
    cdef MPI_Group c_get_group(self)
    cdef int c_get_size(self)
    cdef int c_get_rank(self)
    cdef MPI_Comm c_clone(self)
    
cdef public class Group:

    cdef MPI_Group group


