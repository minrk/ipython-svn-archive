# encoding: utf-8
# -*- test-case-name: ipython1.test.test_multiengine -*-
"""REST web service interface to an IMultiEngine Controller
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

from zope.interface import Interface, implements, Attribute
from twisted.internet import defer, reactor
from twisted.python import components, failure, log

from ipython1.kernel import httputil
from ipython1.external.twisted.web2 import server, channel
from ipython1.external.twisted.web2 import http, resource
from ipython1.external.twisted.web2 import responsecode, stream
from ipython1.external.twisted.web2 import http_headers

from ipython1.kernel import newserialized
from ipython1.kernel import error
from ipython1.kernel.multiengine import \
    MultiEngine, \
    IMultiEngine, \
    ISynchronousMultiEngine

#-------------------------------------------------------------------------------
# The Controller/MultiEngine side of things
#-------------------------------------------------------------------------------

class IHTTPMultiEngineRoot(Interface):
    pass


class HTTPMultiEngineRoot(resource.Resource):

    addSlash = True

    
    def __init__(self, multiengine):
        self.smultiengine = ISynchronousMultiEngine(multiengine)
        self.child_execute = HTTPMultiEngineExecute(self.smultiengine)
        self.child_registerclient = HTTPMultiEngineRegisterClient(self.smultiengine)
        
    #def locateChild(self, request, segments):
    #    log.msg("Segments: " + repr(segments))
    #    return self, ()
    
    def renderHTTP(self, request):
        return http.Response(200, stream=stream.MemoryStream(repr(request)))
    
components.registerAdapter(HTTPMultiEngineRoot,
    IMultiEngine,
    IHTTPMultiEngineRoot)


class HTTPMultiEngineBaseMethod(resource.Resource):

    def __init__(self, smultiengine):
        self.smultiengine = smultiengine
        log.msg("Creating child resource...")
        
    def locateChild(self, request, segments):
        return self, ()
    
    def renderHTTP(self, request):
        return http.Response(200, stream=stream.MemoryStream(repr(request)))
        
    def parseTargets(self, targets):
        if targets == 'all':
            return targets
        elif isinstance(targets, str):
            try:
                engine = int(targets)
            except ValueError:
                pass
            else:
                isGood = self.smultiengine.verifyTargets(engine)
                if isGood:
                    return engine
                else:
                    return False
            targetStringList = targets.split(',')
            try:
                targetList = [int(t) for t in targetStringList]
            except ValueError:
                return False
            else:
                isGood = self.smultiengine.verifyTargets(targetList)
                if isGood:
                    return targetList
                else:
                    return False
        return False
        
    def buildRequestSummary(self, request):
        reply = """host: %r
port: %r
path: %r
prepath: %r
postpath: %r
args: %r
method: %r
headers: %r
""" % (request.host, request.port, request.path, request.prepath, 
       request.postpath, request.args, request.method, request.headers)
        return reply
            
    def packageSuccess(self, result):
        headers, data = httputil.serialize(result)
        response = http.Response(200, stream=stream.MemoryStream(data))
        for k, v in headers.iteritems():
            response.headers.addRawHeader(k, v)
        response.headers.setHeader('content-type', http_headers.MimeType('text', 'plain'))
        return response
        
    def packageFailure(self, f):
        f.cleanFailure()
        headers, data = httputil.serialize(f)
        response = http.Response(200, stream=stream.MemoryStream(data))
        for k, v in headers.iteritems():
            response.headers.addRawHeader(k, v)
        response.headers.setHeader('content-type', http_headers.MimeType('text', 'plain'))
        return response
        
class HTTPMultiEngineExecute(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        targetsString = request.prepath[1]
        targetsArg = self.parseTargets(targetsString)
        lines = request.args['lines'][0]
        clientID = self.smultiengine.registerClient()
        d = self.smultiengine.execute(clientID, True, targetsArg, lines)
        d.addCallback(lambda r: self.packageSuccess(r))
        d.addErrback(lambda f: self.packageFailure(f))
        self.smultiengine.unregisterClient(clientID)
        return d
    
class HTTPMultiEngineRegisterClient(HTTPMultiEngineBaseMethod):
    
    def renderHTTP(self, request):
        clientID = self.smultiengine.registerClient()
        return self.packageSuccess(clientID)
        
class HTTPMultiEngineUnregisterClient(HTTPMultiEngineBaseMethod):
    
    def http_POST(request):
        clientID = request.args.get('clientid')
        

        

        



class IHTTPMultiEngineFactory(Interface):
    pass

    
def HTTPServerFactoryFromMultiEngine(multiengine):
    """Adapt an IMultiEngine to a HTTPServerFactory."""
    s = server.Site(IHTTPMultiEngineRoot(multiengine))
    return channel.HTTPFactory(s)
    
    
components.registerAdapter(HTTPServerFactoryFromMultiEngine,
            IMultiEngine, IHTTPMultiEngineFactory)
        

