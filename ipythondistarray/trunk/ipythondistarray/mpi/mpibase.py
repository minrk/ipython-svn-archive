from mpi4py import MPI

COMM_PRIVATE = MPI.COMM_WORLD.Clone()



__all__ = ['COMM_PRIVATE','MPI']
