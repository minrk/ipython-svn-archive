import os, cPickle as pickle


from nevow import athena, loaders, tags, inevow
from twisted.internet import protocol, reactor
from twisted.python.failure import Failure
from zope.interface import implements

from ipython1.kernel.results import TCPResultsProtocol
from ipython1.kernel.controllerclient import RemoteController

from controllerajaxpb import ResultElement

basedir = os.path.abspath(os.path.curdir)

class TCPAJAXResultsProtocol(TCPResultsProtocol):
    
    def connectionMade(self):
        TCPResultsProtocol.connectionMade(self)
        self.factory.connectionMade(self.transport.getPeer())
    
    def lineReceived(self, line):
        
        msg_split = line.split(" ", 1)
        if msg_split[0] == "RESULT" and len(msg_split) == 2:
            try:
                cmd_tuple = pickle.loads(msg_split[1])
            except pickle.PickleError:
                fail = True
            else:
                fail = False
                self.factory.handleResult(cmd_tuple)
        else:
            fail = True
            
        if fail:
            self.sendLine("RESULT FAIL")
        else:
            self.sendLine("RESULT OK")
    

class TCPAJAXResultsFactory(protocol.ServerFactory):
    protocol = TCPAJAXResultsProtocol
    results = []
    gatherers = []
    
    def connectionMade(self, peer):
        rc = RemoteController((peer.host, 10105))
        rlist = []
        for s in rc.statusAll():
            rlist.extend(s[1].get('history', {}).values())
        for r in rlist:
            self.handleResult(r)
        
    def handleResult(self, result):
        self.results.append(result)
        for g in self.gatherers:
            try:
                g.handleResult(result).addErrback(self.loseGatherer, gatherer=g)
            except:
                self.loseGatherer(gatherer=g)
    
    def addGatherer(self, gatherer):
        self.gatherers.append(gatherer)
        gatherer.source = self
        for r in self.results:
            try:
                gatherer.handleResult(r)
            except:
                return
                
    
    def loseGatherer(self, gatherer=None):
        try:
            self.gatherers.remove(gatherer)
        except ValueError:
            pass
    
myPackage = athena.JSPackage({
    'ControllerModule': basedir+'/controllerajaxpb.js'
    })

athena.jsDeps.mapping.update(myPackage.mapping)

class ResultPage(athena.LivePage):
    addSlash = True
    source = None
    css = open(basedir+'/ajaxpb.css').read()
    
    docFactory = loaders.stan(tags.html[
        tags.head(render=tags.directive('liveglue')),
        tags.style(type="text/css")[css],
        tags.body(render=tags.directive('resultElement'))])
    
    def __init__(self, source):
        athena.LivePage.__init__(self)
        self.source = source
    
    def render_resultElement(self, ctx, data):
        f = ResultElement()
        f.setFragmentParent(self)
        reactor.callLater(.1, self.source.addGatherer, f)
        return ctx.tag[f]
    
class ResultRoot(object):
    implements(inevow.IResource)
    
    def __init__(self, factory):
        self.factory = factory
    
    def locateChild(self, ctx, segments):
        return ResultPage(self.factory), segments
    

