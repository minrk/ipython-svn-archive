#!/usr/bin/env python
# encoding: utf-8

# A super simple example showing how to use all of this in a fully
# asynchronous manner.  The TaskClient also works in this mode.

from twisted.internet import reactor, defer
from ipython1.kernel import asynclient

client = asynclient.AsynMultiEngineClient(('localhost', 10105))

def printer(r):
    print r
    return r

d = client.push(dict(a=5, b='asdf', c=[1,2,3]),targets=0,block=True)
d.addCallback(lambda _: client.pull(('a','b','c'),targets=0,block=True))
d.addBoth(printer)
d.addCallback(lambda _: reactor.stop())
reactor.run()