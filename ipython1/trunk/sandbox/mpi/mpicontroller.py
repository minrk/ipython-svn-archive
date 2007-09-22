from mpi4py import MPI as mpi
import time
from twisted.internet import reactor

print mpi.rank, mpi.size

reactor.run()