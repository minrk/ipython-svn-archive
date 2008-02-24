"""
Perspective Broker Hello, World!
"""
from ipython1.kernel.taskpb import PBTaskClient
from twisted.cred.credentials import UsernamePassword
from twisted.internet import reactor
from twisted.spread import pb
import cPickle as pickle
import ipython1.kernel.api as kernel

def success(message):
    print "Message received:",message
    # reactor.stop()

def failure(error):
    print "error received:", error
    reactor.stop()

def connected(perspective):
    client = PBTaskClient(perspective)
    client.run(kernel.Task('x = "hello"', pull=['x'])).addCallbacks(success, failure)
    client.run(kernel.Task('raise ValueError, "pants"', pull=['x'])).addCallbacks(success, failure)
    print "connected."

factory = pb.PBClientFactory()
reactor.connectTCP("localhost", pb.portno, factory)
factory.login(UsernamePassword("guest", "guest")).addCallbacks(connected, failure)

reactor.run()
