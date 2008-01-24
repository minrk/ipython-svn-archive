import unittest
from ipythondistarray import utils


class TestCreateFactors(unittest.TestCase):
    
    def test12(self):
        f = utils.create_factors(12,size=2)
        self.assertEquals(f,[[2,6],[3,4]])
        f = utils.create_factors(12,size=3)
        self.assertEquals(f,[[2,2,3]])
        f = utils.create_factors(12,size=4)
        self.assertEquals(f,[])