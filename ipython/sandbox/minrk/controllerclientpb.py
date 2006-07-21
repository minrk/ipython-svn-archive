#!/usr/bin python

from twisted.internet import reactor, protocol
from twisted.spread import pb

from ipython1.kernel.remoteengine import Command

factory = pb.PBClientFactory()
reactor.TCPConnect('localhost', 10105, factory)
factory.getRootObject().addCallbacks(connect, fail)

def connect(obj):
    print "connected"
    root = obj
    root.callRemote('')

def fail(reason):
    raise reason

reactor.run()