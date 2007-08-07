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

# import cPickle as pickle
import simplejson, os.path #, urllib

from zope.interface import Interface, implements
from twisted.python import components, failure, log
from twisted.internet import defer

# from ipython1.kernel import error
from ipython1.external.twisted.web2 import server, channel
from ipython1.external.twisted.web2 import http, resource, static
from ipython1.external.twisted.web2 import stream
from ipython1.external.twisted.web2 import http_headers
from ipython1.external import MochiKit

from ipython1.notebook.notebook import INotebookController
from ipython1.notebook import models

#-------------------------------------------------------------------------------
# The Controller side of things
#-------------------------------------------------------------------------------
class MochiDir(resource.Resource):
    def render(self, request):
        return http.Response(200, stream=stream.MemoryStream(repr(request)))

    def locateChild(self, request, segments):
        mochidir = os.path.dirname(MochiKit.__file__)
        name = segments[0]
        fullpath = os.path.join(mochidir, name)
        if os.path.isfile(fullpath) and fullpath[-3:] == '.js':
            return static.File(fullpath), segments[1:]


class IHTTPNotebookServer(Interface):
    pass

class HTTPNotebookServer(static.File):
    
    implements(IHTTPNotebookServer)
    addSlash = True
    
    def __init__(self, nbc):
        self.nbc = nbc
        thisdir = os.path.dirname(__file__)
        static.File.__init__(self, thisdir+'/notebook.html', defaultType="text/html")
        
        self.putChild('connectUser', HTTPNotebookConnectUser(self.nbc))
        self.putChild('disconnectUser', HTTPNotebookDisconnectUser(self.nbc))
        
        self.putChild('addNode', HTTPNotebookAddNode(self.nbc))
        self.putChild('dropNode', HTTPNotebookDropNode(self.nbc))
        self.putChild('getNode', HTTPNotebookGetNode(self.nbc))
        self.putChild('editNode', HTTPNotebookEditNode(self.nbc))
        self.putChild('moveNode', HTTPNotebookMoveNode(self.nbc))
        
        self.putChild('addTag', HTTPNotebookAddTag(self.nbc))
        self.putChild('dropTag', HTTPNotebookDropTag(self.nbc))
        
        self.putChild('addBook', HTTPNotebookAddBook(self.nbc))
        self.putChild('dropBook', HTTPNotebookDropBook(self.nbc))
        self.putChild('getBook', HTTPNotebookAddBook(self.nbc))
        
        self.putChild('addWriter', HTTPNotebookAddWriter(self.nbc))
        self.putChild('dropWriter', HTTPNotebookDropWriter(self.nbc))
        self.putChild('addReader', HTTPNotebookAddReader(self.nbc))
        self.putChild('dropReader', HTTPNotebookDropReader(self.nbc))
        
        self.putChild('bookFromXML', HTTPNotebookFromXML(self.nbc))
        self.putChild('bookToXML', HTTPNotebookToXML(self.nbc))
        
        
        # js/css resources
        self.putChild('notebook.css', static.File(thisdir+'/notebook.css', defaultType="text/css"))
        
        self.mochikit = resource.Resource()
        # self.mochikit.render = renderBack
        # self.mochikit.locateChild = mochiKids
        self.putChild('MochiKit', self.mochikit)
        self.putChild('MochiKit', MochiDir())
        
        self.putChild('notebook.js', static.File(thisdir+'/notebook.js', defaultType="text/javascript"))
    

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
        print request
        print request.args
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
    


################# Node Commands ######################
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
    


class HTTPNotebookAddTag(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            userID = request.args['userID'][0]
            nodeID = request.args['nodeID'][0]
            tag = request.args['tag'][0]
            d = defer.execute(self.nbc.addTag, userID, nodeID, tag)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

class HTTPNotebookDropTag(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            userID = request.args['userID'][0]
            nodeID = request.args['nodeID'][0]
            tag = request.args['tag'][0]
            d = defer.execute(self.nbc.dropTag, userID, nodeID, tag)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    


################# Notebook Commands ######################

class HTTPNotebookAddBook(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            userID = request.args['userID'][0]
            title = request.args['title'][0]
            d = defer.execute(self.nbc.addNotebook, userID, title)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

class HTTPNotebookDropBook(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            userID = request.args['userID'][0]
            nbID = request.args['notebookID'][0]
            d = defer.execute(self.nbc.dropNotebook, userID, nbID)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

class HTTPNotebookGetBook(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            flags = {}
            for k,v in request.args.iteritems():
                if k in ['notebookID']:
                    flags[k] = v[0]
            userID = request.args['userID'][0]
            d = defer.execute(self.nbc.getNotebook, userID, **flags)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

class HTTPNotebookAddWriter(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            userID = request.args['userID'][0]
            nbID = request.args['notebookID'][0]
            writerID = request.args['writerID'][0]
            d = defer.execute(self.nbc.addWriter, userID, nbID, writerID)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

class HTTPNotebookDropWriter(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            userID = request.args['userID'][0]
            nbID = request.args['notebookID'][0]
            writerID = request.args['writerID'][0]
            d = defer.execute(self.nbc.dropWriter, userID, nbID, writerID)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

class HTTPNotebookAddReader(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            userID = request.args['userID'][0]
            nbID = request.args['notebookID'][0]
            readerID = request.args['readerID'][0]
            d = defer.execute(self.nbc.addReader, userID, nbID, readerID)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

class HTTPNotebookDropReader(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            userID = request.args['userID'][0]
            nbID = request.args['notebookID'][0]
            readerID = request.args['readerID'][0]
            d = defer.execute(self.nbc.dropReader, userID, nbID, readerID)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

class HTTPNotebookFromXML(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            userID = request.args['userID'][0]
            xmlstr = request.args['xmlstr'][0]
            d = defer.execute(self.nbc.loadNotebookFromXML, userID, xmlstr)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

def _xmlize(nb):
    return nb.xmlize()

class HTTPNotebookToXML(HTTPNotebookBaseMethod):
    
    def renderHTTP(self, request):
        try:
            userID = request.args['userID'][0]
            nbID = request.args['notebookID'][0]
            d = defer.execute(self.nbc.getNode, userID, notebookID=nbID)
            d.addCallback(_xmlize)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    


########## Twisted Network Code #################

class IHTTPNotebookServerFactory(Interface):
    pass

    
def HTTPServerFactoryFromNotebookController(nbc):
    """Adapt an INotebookController to a HTTPServerFactory."""
    s = server.Site(IHTTPNotebookServer(nbc))
    return channel.HTTPFactory(s)
    

components.registerAdapter(HTTPServerFactoryFromNotebookController,
            INotebookController, IHTTPNotebookServerFactory)


