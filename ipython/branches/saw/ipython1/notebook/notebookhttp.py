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
import urllib, simplejson, os.path

from zope.interface import Interface, implements
from twisted.python import components, failure, log
from twisted.internet import defer

from ipython1.kernel import error
from ipython1.external.twisted.web2 import server, channel
from ipython1.external.twisted.web2 import http, resource, static
from ipython1.external.twisted.web2 import stream
from ipython1.external.twisted.web2 import http_headers

from ipython1.notebook.notebook import INotebookController
from ipython1.notebook import models

#-------------------------------------------------------------------------------
# The Controller side of things
#-------------------------------------------------------------------------------

class IHTTPNotebookServer(Interface):
    pass

class HTTPNotebookServer(static.File):
    
    implements(IHTTPNotebookServer)
    addSlash = True
    
    def __init__(self, nbc):
        self.nbc = nbc
        thisdir = os.path.dirname(__file__)
        static.File.__init__(self, thisdir+'/notebook.html', defaultType="text/html")
        
        self.putChild('connectuser', HTTPNotebookConnectUser(self.nbc))
        self.putChild('disconnectuser', HTTPNotebookDisconnectUser(self.nbc))
        
        self.putChild('addnode', HTTPNotebookAddNode(self.nbc))
        self.putChild('getnode', HTTPNotebookGetNode(self.nbc))
        self.putChild('editnode', HTTPNotebookEditNode(self.nbc))
        self.putChild('movenode', HTTPNotebookMoveNode(self.nbc))
        self.putChild('addroot', HTTPNotebookAddRoot(self.nbc))
        
        self.putChild('notebook.js', static.File(thisdir+'/notebook.js', defaultType="text/javascript"))
        self.putChild('notebook.css', static.File(thisdir+'/notebook.css', defaultType="text/css"))
    

components.registerAdapter(HTTPNotebookServer,
        INotebookController, IHTTPNotebookServer)

def jsonifyFailure(f):
    d = {}
    d['message'] = f.value.message
    d['traceback'] = f.getTraceback()
    return d

class HTTPNotebookBaseMethod(resource.Resource):
    
    def __init__(self, nbc):
        self.nbc = nbc
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
        data = simplejson.dumps(jsonifyFailure(f))
        response = http.Response(200, stream=stream.MemoryStream(data))
        response.headers.setHeader('content-type', http_headers.MimeType('text', 'plain'))
        return response
    

# User classes
class HTTPNotebookConnectUser(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            uname = request.args['username'][0]
            email = request.args['email'][0]
            if not email:
                email = None
            d = defer.execute(self.nbc.connectUser, uname, email)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

class HTTPNotebookDisconnectUser(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            userID = request.args['userID'][0]
            d = defer.execute(self.nbc.disconnectUser, userID)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

# class HTTPNotebookEditUser(HTTPNotebookBaseMethod):
#     
#     def renderHTTP(self, request):
#         try:
#             uid = request.args['userID'][0]
#             if request.args.get('drop'):
#                 self.nbc.dropUser(userID=uid)
#             else:
#                 uname = request.args['username'][0]
#                 email = request.args['email'][0]
#                 user = self.nbc.getUser(userID=uid)
#                 user.username = uname
#                 user.email = email
#                 self.nbc.session.save(user)
#                 self.nbc.session.flush()
#         except Exception, e:
#             return self.packageFailure(failure.Failure(e))
#         else:
#             d = defer.succeed(None)
#             d.addCallbacks(self.packageSuccess, self.packageFailure)
#             return d

class HTTPNotebookGetNode(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            flags = {}
            for k,v in request.args.iteritems():
                if k in ['nodeID','parentID','textData', 'input', 'nodeType'
                        'output','comment', 'nextID', 'previousID']:
                    flags[k] = v[0]
            userID = request.args['userID'][0]
            d = defer.execute(self.nbc.getNode, userID, **flags)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

class HTTPNotebookAddNode(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            userID = request.args['userID'][0]
            parentID = request.args['parentID'][0]
            nodeType = request.args['nodeType'][0]
            index = request.args['index']
            
            flags = {}
            for k,v in request.args.iteritems():
                if k in ['textData', 'input',
                        'output','comment', 'nextID', 'previousID']:
                    flags[k] = v[0]
            node = getattr(models, nodeType)()
            for k,v in flags.iteritmes():
                setattr(node,k,v)
            d = defer.execute(self.nbc.addNode, userID, parentID, node, index)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

class HTTPNotebookEditNode(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            userID = request.args['userID'][0]
            nodeID = request.args['nodeID'][0]
            flags = {}
            for k,v in request.args.iteritems():
                if k in ['textData', 'input', 'parentID',
                        'output','comment', 'nextID', 'previousID']:
                    flags[k] = v[0]
            d = defer.execute(self.nbc.editNode, userID, nodeID, **flags)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d = defer.succeed(None)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

class HTTPNotebookDropNode(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            userID = request.args['userID'][0]
            nodeID = request.args['nodeID'][0]
            d = defer.execute(self.nbc.dropNode, userID, nodeID)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    
class HTTPNotebookMoveNode(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            userID = request.args['userID'][0]
            nodeID = request.args['nodeID'][0]
            parentID = request.args['parentID'][0]
            index = request.args['index'][0]
            d = defer.execute(self.nbc.moveNode, userID, nodeID, parentID, index)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

class HTTPNotebookAddRoot(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            userID = request.args['userID'][0]
            title = request.args['title'][0]
            d = defer.execute(self.nbc.addRoot, userID, title)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    


class IHTTPNotebookServerFactory(Interface):
    pass

    
def HTTPServerFactoryFromNotebookController(nbc):
    """Adapt an INotebookController to a HTTPServerFactory."""
    s = server.Site(IHTTPNotebookServer(nbc))
    return channel.HTTPFactory(s)
    

components.registerAdapter(HTTPServerFactoryFromNotebookController,
            INotebookController, IHTTPNotebookServerFactory)


