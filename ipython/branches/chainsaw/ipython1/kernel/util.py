#!/usr/bin/env python
# encoding: utf-8
"""
util.py

Created by Brian Granger on 2006-08-10.
Copyright (c) 2006 __MyCompanyName__. All rights reserved.
"""

#from twisted.defer.gatherresults/_parseDlist
def parseResults(results):
    return [x[1] for x in results]

def gatherBoth(dlist):
    d = defer.DeferredList(dlist, consumeErrors=1)
    d.addCallback(parseResults)
    return d

