class Iterator(object):

    def __init__(self,a):
        """Simple iterator."""
        self.aiter = iter(a)

    def __iter__(self):
        return self
    
    def next(self):
        return self.aiter.next()


def iterator(a):
    """Simple generator"""
    aiter = iter(a)
    while True:
        yield aiter.next()

class RemoteIterator(object):

    def __init__(self,rc,engine,name):
        """Return an iterator on an object living on a remote engine.
        """
        # Check that the object exists on the remote engine and pin a reference
        # to it
        iter_name = '_%s_rmt_iter_' % name
        rc.execute(engine,'%s = iter(%s)' % (iter_name,name))
        
        self.rc = rc
        self.engine = engine
        self.name = name
        self.iter_name = iter_name

    def __iter__(self):
        return self

    def next(self):
        self.rc.execute(self.engine,'_tmp = %s.next()' % self.iter_name)
        return self.rc.pull(self.engine,'_tmp')[0]

        
# main
aa = range(3,8)
bb = Iterator(aa)
cc = iterator(aa)

print 'Original aa:'
print aa

print 'Contents of bb:'
for k in bb: print k,
print

print 'Contents of cc:'
for k in cc: print k,
print
