from ipythondistarray.core.tests.common import *
from ipythondistarray.core import functions
from ipythondistarray.core import maps, distarray

class TestFoo(unittest.TestCase):
    
    def test_arecompatible(self):
        """
        Test if two DistArrays are compatible.
        """
        comm = create_comm(4)
        if not comm==MPI.COMM_NULL:
            a = distarray.DistArray((16,16),dtype='int64')
            b = distarray.DistArray((16,16),dtype='float32')
            self.assertEquals(functions.arecompatible(a,b), True)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass