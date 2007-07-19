# encoding: utf-8
# -*- test-case-name: ipython1.test.test_multiengine -*-
"""REST web service interface to an INotebookController
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
import httplib2, urllib, simplejson, os.path

from zope.interface import Interface, implements
from twisted.python import components, failure, log

from ipython1.kernel import error
from ipython1.external.twisted.web2 import server, channel
from ipython1.external.twisted.web2 import http, resource, static
from ipython1.external.twisted.web2 import stream
from ipython1.external.twisted.web2 import http_headers

from ipython1.notebook.notebook import INotebookController
from ipython1.notebook.models import tformat

#-------------------------------------------------------------------------------
# The Controller side of things
#-------------------------------------------------------------------------------

class IHTTPNotebookServer(Interface):
    pass

class HTTPNotebookServer(static.File):
    
    implements(IHTTPNotebookRoot)
    addSlash = True
    
    def __init__(self, nbs):
        self.nbs = nbs
        static.File.__init__(self, os.path.dirname(__file__)+'notebook.html', defaultType="text/html")
        
        self.child_adduser = HTTPNotebookAddUser(self.nbs)
        self.child_getuser = HTTPNotebookGetUser(self.nbs)
        self.child_edituser = HTTPNotebookEditUser(self.nbs)
        self.child_addnode = HTTPNotebookAddBook(self.nbs)
        self.child_getnode = HTTPNotebookGetBook(self.nbs)
        self.child_editnode = HTTPNotebookEditBook(self.nbs)
        
        self.putChild('notebook.js', static.File(os.path.dirname(__file__)+'notebook.js', defaultType="text/javascript"))
    

components.registerAdapter(HTTPNotebookServer,
        INotebookServer, IHTTPNotebookServer)

def jsonifyFailure(f):
    d = {}
    d['message'] = f.value.message
    d['traceback'] = f.getTraceback()
    return d

class HTTPNotebookBaseMethod(resource.Resource):
    
    def __init__(self, nbs):
        self.nbs = nbs
        log.msg("Creating child resource...")
    
    def locateChild(self, request, segments):
        return self, ()
    
    def renderHTTP(self, request):
        return http.Response(200, stream=stream.MemoryStream(repr(request)))
    
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
        try:
            data = result.jsonify()
        except AttributeError:
            data = simplejson.dumps(result)
        response = http.Response(200, stream=stream.MemoryStream(data))
        response.headers.setHeader('content-type', http_headers.MimeType('text', 'plain'))
        return response
    
    def packageFailure(self, f):
        f.cleanFailure()
        data = simpleson.dumps(jsonifyFailure(f))
        response = http.Response(200, stream=stream.MemoryStream(data))
        response.headers.setHeader('content-type', http_headers.MimeType('text', 'plain'))
        return response
    

# User classes
class HTTPNotebookGetUser(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            flags = {}
            for k,v in request.args.iteritems():
                if k in ['userID', 'username', 'email']:
                    flags[k] = v[0]
            d = defer.execute(self.nbs.getUser, **flags)
            d = defer.execute(self.nbs.getUser, username=uname)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

class HTTPNotebookAddUser(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            uname = request.args['username'][0]
            email = request.args['email'][0]
            d = defer.execute(self.nbs.addUser, uname, email)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

class HTTPNotebookEditUser(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            uid = request.args['userID'][0]
            if request.args.get('drop'):
                self.nbs.dropUser(userID=uid)
            else:
                uname = request.args['username'][0]
                email = request.args['email'][0]
                user = self.nbs.getUser(userID=uid)
                user.username = uname
                user.email = email
                self.nbs.session.save(user)
                self.nbs.session.flush()
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d = defer.succeed(None)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d

class HTTPNotebookGetNode(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            flags = {}
            for k,v in request.args.iteritems():
                if k in ['nodeID','parentID','userID','textData', 'input',
                        'output',]
                    flags[k] = v[0]
            d = defer.execute(self.nbs.getNode, **flags)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

class HTTPNotebookAddNode(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            # resolve parent
            
            # create node
            
            # d = defer.execute( nbs.addChild, node, parent, indices)
            
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

class HTTPNotebookEditNode(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            uid = request.args['userID'][0]
            if request.args.get('drop'):
                self.nbs.dropUser(userID=uid)
            else:
                uname = request.args['username'][0]
                email = request.args['email'][0]
                user = self.nbs.getUser(userID=uid)
                user.username = uname
                user.email = email
                self.nbs.session.save(user)
                self.nbs.session.flush()
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d = defer.succeed(None)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

class IHTTPNotebookServerFactory(Interface):
    pass

    
def HTTPServerFactoryFromNotebookServer(nbserver):
    """Adapt an INotebookController to a HTTPServerFactory."""
    s = server.Site(IHTTPNotebookServer(nbserver))
    return channel.HTTPFactory(s)
    

components.registerAdapter(HTTPServerFactoryFromNotebookController,
            INotebookServer, IHTTPNotebookServerFactory)


