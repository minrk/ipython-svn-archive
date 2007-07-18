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
from ipython1.notebook.xmlutil import tformat

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
        self.child_addbook = HTTPNotebookAddBook(self.nbs)
        self.child_getbook = HTTPNotebookGetBook(self.nbs)
        self.child_editbook = HTTPNotebookEditBook(self.nbs)
        self.child_addcell = HTTPNotebookAddCell(self.nbs)
        self.child_getcell = HTTPNotebookGetCell(self.nbs)
        self.child_editcell = HTTPNotebookEditCell(self.nbs)
        
        self.putChild('notebook.js', static.File(os.path.dirname(__file__)+'notebook.js', defaultType="text/javascript"))
    

components.registerAdapter(HTTPNotebookServer,
        INotebookServer, IHTTPNotebookServer)

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
        data = simplejson.dumps(IJSonDict(result))
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
            uname = request.args['username'][0]
            user = self.nbs.getUser(uname)
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            
            d = self.nbs.run(task)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

class HTTPNotebookBook(HTTPNotebookBaseMethod):
    
    def __init__(self, nbs):
        super(HTTPNotebookBook, self).__init__(nbs)
        self.child_get = HTTPNotebookBookGet(self.nbs)
        self.child_put = HTTPNotebookBookPut(self.nbs)
    
    def renderHTTP(self, request):
        try:
            taskID = int(request.args['taskID'][0])
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d = self.nbs.abort(taskID)
            d.addCallbacks(self.packageSuccess, self.packageFailure)
            return d
    

class HTTPNotebookCell(HTTPNotebookBaseMethod):
    
    def __init__(self, nbs):
        super(HTTPNoteCellCell, self).__init__(nbs)
        self.child_add = HTTPNoteBookCellAdd(self.nbs)
        self.child_drop = HTTPNoteBookCellDrop(self.nbs)
    
    def renderHTTP(self, request):
        try:
            taskID = int(request.args['taskID'][0])
        except Exception, e:
            return self.packageFailure(failure.Failure(e))
        else:
            d = self.nbs.getNotebookResult(taskID)
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



#-------------------------------------------------------------------------------
# JSON utilities
#-------------------------------------------------------------------------------

class IJSONDict(zi.Interface):
    pass

def jsonStarter(obj):
    d = {}
    d['dateCreated'] = obj.dateCreated.strftime(tformat)
    d['dateModified'] = obj.dateModified.strftime(tformat)
    return d

def jsonifyUser(u):
    d = jsonStarter(u)
    d['userID'] = u.userID
    d['username'] = u.username
    d['email'] = u.email
    d['notebooks'] = [nb.title for nb in u.notebooks]
    return d

def jsonifyNotebook(nb):
    d = jsonStarter(nb)
    d['username'] = nb.user.username
    d['email'] = nb.user.email
    d['root'] = IJSONDict(nb.root)
    return d

def jsonCell(c):
    d = jsonStarter(c)
    for key in ['cellID', 'parentID', 'nextID', 'previousID', 'comment']:
        d[key] = getattr(c, key)
    return d

def jsonifyMultiCell(mc):
    d = jsonCell(mc)
    d['title'] = mc.title
    d['children'] = [mc[i].cellID for i in range(len(mc.children))]
    return d

def jsonifyTextCell(tc):
    d = jsonCell(tc)
    d['textData'] = tc.textData
    return d

def jsonifyInputCell(ic):
    d = jsonCell(ic)
    d['input'] = ic.input
    d['output'] = ic.output
    return d

def jsonifyFailure(f):
    d = {}
    d['message'] = f.value.message
    d['traceback'] = f.getTraceback()
    return d
    
components.registerAdapter(jsonifyUser, models.IUser, IJSONDict)
components.registerAdapter(jsonifyMultiCell, models.IMultiCell, IJSONDict)
components.registerAdapter(jsonifyTextCell, models.ITextCell, IJSONDict)
components.registerAdapter(jsonifyInputCell, models.IInputCell, IJSONDict)


