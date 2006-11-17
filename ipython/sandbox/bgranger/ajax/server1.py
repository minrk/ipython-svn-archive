#!/usr/bin/env python
# encoding: utf-8
"""
server1.py

C
"""
import sys
from twisted.web import server, resource
from twisted.internet import reactor
from twisted.python import log

from twisted.web import server, resource
from twisted.internet import reactor

class Simple(resource.Resource):
    isLeaf = True
    
    def getChild(self, path, request):
        log.msg(path)
        return self
        
    def render_GET(self, request):
        #request.write(request.args['a'])
        a = int(request.args['a'][0])
        b = int(request.args['b'][0])
        return str(a+b)
        return "<html>%s %s %s %s</html>" % \
            (request.method, request.uri, request.path, repr(request.args))

site = server.Site(Simple())
reactor.listenTCP(8080, site)
log.startLogging(sys.stdout)
reactor.run()