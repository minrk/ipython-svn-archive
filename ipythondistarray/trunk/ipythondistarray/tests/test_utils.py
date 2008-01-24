import unittest
from ipythondistarray import utils


class TestMultPartitions(unittest.TestCase):
    
    def test_both_methods(self):
        for s in [2,3]:
            for n in range(2, 512):
                self.assertEquals(utils.mult_partitions(n,s), utils.create_factors(n,s))
