#!/usr/bin/env python

from twisted.spread import pb
from twisted.internet import reactor

def gotObject(object):
    print "got object:", object
    object.callRemote("put_pickle","a",3).addCallback(gotData)
# or
#   object.callRemote("getUsers").addCallback(gotData)
   
def gotData(data):
    print 'server sent:', data
    reactor.stop()
    
def gotNoObject(reason):
    print "no object:",reason
    reactor.stop()

factory = pb.PBClientFactory()
reactor.connectTCP("127.0.0.1",10105, factory)
factory.getRootObject().addCallbacks(gotObject,gotNoObject)
reactor.run()
