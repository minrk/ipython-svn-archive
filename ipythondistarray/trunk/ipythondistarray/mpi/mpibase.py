from mpi4py import MPI

__all__ = [
    'COMM_PRIVATE',
    'MPI',
    'create_comm_of_size']


COMM_PRIVATE = MPI.COMM_WORLD.Clone()

def create_comm_of_size(size=4):

    group = COMM_PRIVATE.Get_group()
    comm_size = COMM_PRIVATE.Get_size()
    if size > comm_size:
        return MPI.COMM_NULL
    else:
        subgroup = group.Incl(range(size))
        newcomm = COMM_PRIVATE.Create(subgroup)
        return newcomm