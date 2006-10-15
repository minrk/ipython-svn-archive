"""
Serialization objects and utilities for use in network protocols.

TODO:  allow discontinuous array buffers (in ArraySerialized.packObj)
       The restriction is actually in EnhancedNetstring.
"""
__docformat__ = "restructuredtext en"
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

import cPickle as pickle

def serialize(obj, key):
    """Serialize obj using an appropriate subclass of Serialized."""
    
    serial = None
    try:
        import numpy
    except ImportError:
        pass
    else:
        if isinstance(obj, numpy.ndarray):
            serial = ArraySerialized(key)
            serial.packObject(obj)
            return serial
    serial = PickleSerialized(key)
    serial.packObject(obj)
    return serial

class Serialized(object):
    """A class to hold serialized objects in different formats.
    
    The most general form of a serialized object is a sequence of strings.
    """
    
    package = []
    
    def __init__(self, key):
        self.key = key
        self.initPackage()
    
    def __getitem__(self, index):
        return self.package.__getitem__(index)
    
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
    """Class for holding pickled objects."""
        
    def initPackage(self):
        self.package = ['PICKLE %s' % self.key]
    
    def packObject(self, obj):
        p = pickle.dumps(obj, 2)
        self.package.append(p)
    
    def unpack(self):
        return pickle.loads(self.package[1])
    
# Only define ArraySerialized is numpy is available
try:
    import numpy
except ImportError:
    pass
else:
    class ArraySerialized(Serialized):
        """Class for holding serialized numpy arrays."""
        
        def initPackage(self):
            self.package = ['ARRAY %s' % self.key]
        
        def packObject(self, obj):
            if not isinstance(obj, numpy.ndarray):
                raise TypeError('obj must be a numpy ndarray object')
            # Our send method requires contiguous arrays, so if it is not
            # contiguous, we must make a contiguous copy, which is undesirable
            array = numpy.ascontiguousarray(obj, dtype=None)
            p = []
            p.append(pickle.dumps(array.shape, 2))
            p.append(array.dtype.str)
            p.append(numpy.getbuffer(array))   # I think we are making a copy!
            self.package.extend(p)
        
        def unpack(self):
            result = numpy.frombuffer(self.package[3], dtype = self.package[2])
            result.shape = pickle.loads(self.package[1])
            return result
        
    
