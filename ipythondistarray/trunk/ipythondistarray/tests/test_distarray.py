import unittest
from ipythondistarray import maps, distarray

class TestInit(unittest.TestCase):
    
    def testa(self):
        da = distarray.DistArray((16,16),dist={0:'b',1:'b'},grid_shape=(2,2))

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
	

