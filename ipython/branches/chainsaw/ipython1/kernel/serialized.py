import cPickle as pickle

class Serialized(object):

    def __init__(self, key):
        self.key = key
        self.initPackage()

    def initPackage(self):
        raise NotImplementedError('Use a concrete sublcass of Serialized')        

    def packObject(self, obj):
        """Must set add to self.serializedObject"""
        raise NotImplementedError('Use a concrete sublcass of Serialized')
   
    def addToPackage(self, *args):
        self.package.extend(args)
        
    def unpack(self):
        """ return an unserialized object from self.serializedObject"""
        raise NotImplementedError('Use a concrete sublcass of Serialized')
        
    def __iter__(self):
        return self.package.__iter__()
        
class PickleSerialized(Serialized):
        
    def initPackage(self):
        self.package = ['PICKLE %s' % self.key]
        
    def packObject(self, obj):
        p = pickle.dumps(obj, 2)
        self.package.append(p)
        
    def unpack(self):
        return pickle.loads(self.package[1])

try:
    import numpy
except ImportError:
    pass
else:
    class ArraySerialized(Serialized):
    
        def initPackage(self):
            self.package = ['ARRAY %s' % self.key]
    
        def packObject(self, obj):
            if not isinstance(obj, numpy.ndarray):
                raise TypeError('obj must be a numpy ndarray object')
                
            p = []
            p.append(pickle.dumps(obj.shape, 2))
            p.append(obj.dtype.str)
            p.append(numpy.getbuffer(obj))   # I think we are making a copy!
            self.package.extend(p)
        
        def unpack(self):
            result = numpy.frombuffer(self.package[3], dtype = self.package[2])
            result.shape = pickle.loads(self.package[1])
            return result

