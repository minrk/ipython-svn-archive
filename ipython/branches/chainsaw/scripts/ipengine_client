#!/usr/bin/env python

from twisted.spread import pb
from twisted.internet import reactor
from IPython.genutils import clock, clock2

def gotObject(object):
    print "got object:", object, clock()
    
    for reps in range(100):
        object.callRemote("put","b",10).addCallback(gotData)
    object.callRemote("put","c",10).addCallback(halt)
    
def halt(data):
    print clock()
    reactor.stop()
   
def gotData(data):
    pass
    #print 'server sent:', data
    #reactor.stop()
    
def gotNoObject(reason):
    print "no object:",reason
    reactor.stop()

factory = pb.PBClientFactory()
reactor.connectTCP("127.0.0.1",10105, factory)
factory.getRootObject().addCallbacks(gotObject,gotNoObject)
reactor.run()
