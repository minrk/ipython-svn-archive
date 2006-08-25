#!/usr/bin/env python
# encoding: utf-8

#*****************************************************************************
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from twisted.internet import defer
from ipython1.kernel import serialized


#from twisted.internet.defer.gatherresults/_parseDlist
def parseResults(results):
    return [x[1] for x in results]

def gatherBoth(dlist):
    d = defer.DeferredList(dlist, consumeErrors=1)
    d.addCallback(parseResults)
    return d

#from the Python Cookbook:
def curry(f, *curryArgs, **curryKWargs):
    def curried(*args, **kwargs):
        dikt = dict(kwargs)
        dikt.update(curryKWargs)
        return f(*(curryArgs+args), **dikt)
    
    return curried

#useful callbacks
def printer(r):
    print r
    return r

def unpack(serial):
    if isinstance(serial, list):
        return [s.unpack() for s in serial]
    if isinstance(serial, Serialized):
        return serial.unpack()
    return serial
