import unittest
from ipythondistarray import maps

class TestMapBase(unittest.TestCase):
    
    def test_init(self):
        m = maps.Map(16,4)
        self.assertEquals(m.local_shape,4)
        m = maps.Map(17,4)
        self.assertEquals(m.local_shape,5)
        m = maps.Map(15,4)
        self.assertEquals(m.local_shape,4)

class TestBlockMap(unittest.TestCase):
    
    def test_owner(self):
        m = maps.BlockMap(16,4)
        owners = [m.owner(e) for e in range(16)]
        self.assertEquals(4*[0]+4*[1]+4*[2]+4*[3],owners)
        m = maps.BlockMap(17,4)
        owners = [m.owner(e) for e in range(17)]
        self.assertEquals(5*[0]+5*[1]+5*[2]+2*[3],owners)        
        m = maps.BlockMap(15,4)
        owners = [m.owner(e) for e in range(15)]
        self.assertEquals(4*[0]+4*[1]+4*[2]+3*[3],owners)
        
    def test_local_index(self):
        m = maps.BlockMap(16,4)
        p = [m.local_index(i) for i in range(16)]
        self.assertEquals(4*range(4),p)
        m = maps.BlockMap(17,4)
        p = [m.local_index(i) for i in range(17)]
        self.assertEquals(4*range(4)+[0],p)
        m = maps.BlockMap(15,4)
        p = [m.local_index(i) for i in range(15)]
        self.assertEquals(3*range(4)+[0,1,2],p)
        
class TestCyclicMap(unittest.TestCase):
     
    def test_owner(self):
        m = maps.CyclicMap(16,4)
        owners = [m.owner(e) for e in range(16)]
        self.assertEquals(4*range(4),owners)
        m = maps.CyclicMap(17,4)
        owners = [m.owner(e) for e in range(17)]
        self.assertEquals(4*range(4)+[0],owners)
        m = maps.CyclicMap(15,4)
        owners = [m.owner(e) for e in range(15)]
        self.assertEquals(3*range(4)+[0,1,2],owners)
    
    def test_local_index(self):
        m = maps.CyclicMap(16,4)
        p = [m.local_index(i) for i in range(16)]
        self.assertEquals(4*[0]+4*[1]+4*[2]+4*[3],p)
        m = maps.CyclicMap(17,4)
        p = [m.local_index(i) for i in range(17)]
        self.assertEquals(4*[0]+4*[1]+4*[2]+4*[3]+[4],p)
        m = maps.CyclicMap(15,4)
        p = [m.local_index(i) for i in range(15)]
        self.assertEquals(4*[0]+4*[1]+4*[2]+3*[3],p)

class TestRegistry(unittest.TestCase):
    
    def test_get_class(self):
        mc = maps.get_map_class('b')
        self.assertEquals(mc,maps.BlockMap)
        mc = maps.get_map_class('c')
        self.assertEquals(mc,maps.CyclicMap)
        mc = maps.get_map_class('bc')
        self.assertEquals(mc,maps.BlockCyclicMap)
    
    def test_get_class_pass(self):
        mc = maps.get_map_class(maps.BlockMap)
        self.assertEquals(mc, maps.BlockMap)