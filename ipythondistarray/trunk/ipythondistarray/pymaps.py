class Map(object):
    
    def __init__(self, nglobal, nprocs):
        self.nglobal = nglobal
        self.nprocs = nprocs
        self.nlocal = self.nglobal/self.nprocs
        if self.nglobal%self.nprocs > 0:
            self.nlocal += 1
    
    def owner(self, global_i):
        raise NotImplemented("implement in sublcass")
        
    def local_i(self, global_i):
        raise NotImplemented("implement in sublcass")
        
    def global_i(self, owner, local_i):
        raise NotImplemented("implement in sublcass")


class BlockMap(Map):
        
    def owner(self, global_i):
        return global_i/self.nlocal
        
    def local_i(self, global_i):
        local_i = global_i%self.nprocs
        return self.owner(global_i), local_i
        
    def global_i(self, owner, local_i):
        return owner*self.nlocal + local_i
        
def test1():
    m = BlockMap(16,4)
    for i in range(10000):
        m.owner(3)

