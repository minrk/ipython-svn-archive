from mpi4py import MPI as mpi
import time
from twisted.internet import reactor

rank = mpi.COMM_WORLD.Get_rank()
size = mpi.COMM_WORLD.Get_size()

def runController(self):
    reactor.call

if rank==0:
    runner = runController
else:
    runner = runEngine

reactor.callWhenRunning(runner)
reactor.run()