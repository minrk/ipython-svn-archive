# encoding: utf-8
# -*- test-case-name: ipython1.test.test_multiengine -*-
"""HTTP Utilities
"""
__docformat__ = "restructuredtext en"
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelley <benjaminrk@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import cPickle as pickle
import xmlrpclib
import httplib
import urllib
import base64

from ipython1.external.twisted.web2 import server, channel
from ipython1.external.twisted.web2 import http, resource
from ipython1.external.twisted.web2 import responsecode, stream
from ipython1.external.twisted.web2 import http_headers

from ipython1.kernel import newserialized


#-------------------------------------------------------------------------------
# The Controller/MultiEngine side of things
#-------------------------------------------------------------------------------

def serialize(obj):
    serial = newserialized.serialize(obj)
    data = serial.getData()
    typeDescriptor = serial.getTypeDescriptor()
    md = serial.getMetadata()
    headers = {'serial-type': typeDescriptor}
    if typeDescriptor == 'ndarray':
        headers['dtype'] = md['dtype']
        headers['shape'] = base64.encodestring(pickle.dumps(md['shape'],2))
    headers = prefixHeaders(headers)
    return headers, data
    
def prefixHeaders(dikt, prefix='x-ipy-'):
    newDikt = {}
    for k, v in dikt.iteritems():
        newDikt[prefix + k] = v
    return newDikt

