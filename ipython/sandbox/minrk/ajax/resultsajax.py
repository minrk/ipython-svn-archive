import os, cPickle as pickle


from nevow import athena, loaders, tags, inevow
from twisted.internet import protocol, reactor
from twisted.python.failure import Failure
from zope.interface import implements


from ipython1.kernel.results import TCPResultsProtocol
from ipython1.kernel.controllerclient import RemoteController


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
    'ResultModule': os.path.abspath(os.path.curdir)+'/resultmodule.js'
    })

athena.jsDeps.mapping.update(myPackage.mapping)

class ResultElement(athena.LiveElement):
    jsClass = u'ResultModule.ResultWidget'
    
    docFactory = loaders.stan([tags.div(render=tags.directive('liveElement')),
        tags.div(id="output")])
    
    def resultToHTML(self, cmd):
        s=''
        if isinstance(cmd, Failure):
            s+="Failure"
        else:
            target = cmd[0]
            cmd_num = cmd[1]
            cmd_stdin = cmd[2]
            cmd_stdout = cmd[3][:-1]
            cmd_stderr = cmd[4][:-1]
            s += "<a id='stdin'>[%i]In [%i]:</a> %s<br>" % (target, cmd_num, cmd_stdin)
            if cmd_stdout:
                s += "<a id='stdout'>[%i]Out[%i]:</a> %s<br>" % (target, cmd_num, cmd_stdout)
            if cmd_stderr:
                s += "<a id='stderr'>[%i]Err[%i]:</a><br> %s<br>" % (target, cmd_num, cmd_stderr)
        return unicode(s)
    
    def handleResult(self, result):
        us = self.resultToHTML(result)
        return self.callRemote('handleResult', us)
    

style = """

#output{
    border: 1px solid #999;
    margin-top: 2em;
    margin-left: auto;
    margin-right: auto;
	overflow: auto;
	width: 480px;
	height: 420px;
	text-align: left;
    font-family: monospace;
}

#stdin{
	color: green;
	font-weight: bold;
}
#stdout{
	color: blue;
	font-weight: bold;
}
#stderr{
	color: red;
	font-weight: bold;
}
"""
class ResultPage(athena.LivePage):
    addSlash = True
    source = None
    
    docFactory = loaders.stan(tags.html[
        tags.head(render=tags.directive('liveglue')),
        tags.style(render=tags.directive('style')),
        tags.body(render=tags.directive('resultElement'))])
    
    def __init__(self, source):
        athena.LivePage.__init__(self)
        self.source = source
    
    def render_style(self, ctx, data):
        f = style
        return ctx.tag[f]
    
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
    

