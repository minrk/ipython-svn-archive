import os, cPickle as pickle


from nevow import athena, loaders, tags, inevow
from twisted.internet import protocol, reactor
from twisted.spread import pb
from twisted.python.failure import Failure
from zope.interface import implements

from ipython1.kernel import controllerpb as cpb

basedir = os.path.abspath(os.path.curdir)

myPackage = athena.JSPackage({
    'ControllerModule': basedir+'/controllerajaxpb.js'
    })

athena.jsDeps.mapping.update(myPackage.mapping)

class ControllerElement(athena.LiveElement):
    jsClass = u'ControllerModule.ControllerWidget'
    
    docFactory = loaders.stan(tags.div(render=tags.directive('liveElement'))[
        # tags.input(type="submit", value="testclick", onclick="""
        # try{var c = Nevow.Athena.Widget.get(this);alert(c);}
        # catch(err){alert(err.description)}"""),
        tags.table(id="command")[
        tags.tr[tags.td["cmd"],tags.td["targets"], tags.td["args"]],
        tags.tr[tags.form(id="cmdform",
            action="""javascript:
            var w = Nevow.Athena.Widget.get(getElement('cmdform'));
            var cmd = getElement('cmd');
            cmd = cmd.options[cmd.selectedIndex].value;
            var targets = getElement('targets').value;
            var args = getElement('args').value;
            w.submitCommand(cmd, targets, args);""")[
            
            tags.td[tags.select(id="cmd", name="cmd",
            onchange="Nevow.Athena.Widget.get(this).changeCmd(this.options[cmd.selectedIndex].value);")[
                tags.option(value="execute")["execute"],
                tags.option(value="pull")["pull"],
                tags.option(value="status")["status"],
                tags.option(value="reset")["reset"],
                tags.option(value="kill")["kill"],
            ]],
            tags.td[tags.input(type="text", id="targets", name="targets", value="all")],
            tags.td[tags.input(type="text", id="args", name="args")],
            tags.td[tags.input(type="submit", value="exec")]
        ]],
        tags.tr[tags.td(colspan='3', style="text-align: center")[tags.div(id="commandout")]]
        ]
    ])
    
    def __init__(self, controller):
        self.controller = controller
    
    def parseTargets(self, targets):
        if targets == 'all':
            return 'all'
        try:
            return map(int,targets.split(','))
        except ValueError:
            return False
    
    def execute(self, targets, lines):
        idlist = self.parseTargets(targets)
        if idlist is False:
            return self.Fail(None)
        d = self.controller.execute(idlist, lines)
        return d.addCallbacks(self.executeOK, self.Fail)
    
    athena.expose(execute)
    
    def executeOK(self, resultList):
        s = ''
        for r in resultList:
            s += self.resultToHTML(r)
        self.callRemote('commandOutput', unicode(s))
    
    def status(self, targets, _):
        idlist = self.parseTargets(targets)
        if not idlist:
            return self.Fail(None)
        d = self.controller.status(idlist)
        return d.addCallbacks(self.statusOK, self.Fail)
    
    athena.expose(status)
    
    def statusOK(self, resultList):
        s = "<table id='status'><tr><td><b>id</b></td>\
        <td><b>queue</b></td><td><b>history</b></td><td><b>locals</b></td></tr>\n"
        for r in resultList:
            s += '<tr><td>%i</td>'%r[0]
            s += self.statusToHTML(r[1])
            s += '</tr>'
        return self.callRemote('commandOutput', unicode(s+'</table>'))
    
    def pull(self, targets, keystr):
        keys = map(str, keystr.split(','))
        idlist = self.parseTargets(targets)
        if not idlist or not keys:
            return self.Fail(None)
        d = self.controller.pullNamespace(idlist, *keys)
        return d.addCallbacks(self.pullOK, self.Fail)
    
    athena.expose(pull)
    
    def pullOK(self, resultList):
        s = ''
        print resultList
        for r in resultList:
            s += self.dictToHTML(r)
        return self.callRemote('commandOutput', unicode(s))
    
    def reset(self, targets, _):
        idlist = self.parseTargets(targets)
        if not idlist:
            return self.Fail(None)
        d = self.controller.reset(idlist)
        return d.addCallbacks(self.resetOK, self.Fail)
    
    athena.expose(reset)
    
    def resetOK(self, r):
        return self.callRemote('commandOutput', u'')
    
    def kill(self, targets, _):
        idlist = self.parseTargets(targets)
        if not idlist:
            return self.Fail(None)
        d = self.controller.kill(idlist)
        return d.addCallbacks(self.killOK, self.Fail)
    
    athena.expose(kill)
    
    def killOK(self, r):
        return self.callRemote('commandOutput', u'')
    
    def Fail(self, f):
        self.callRemote('commandOutput', u'Failure')    
    
    def statusToHTML(self, status):
        s ="<td  id='statuselement'>"
        if not status.get('queue', None):
            s+= "&nbsp"
        else:
            for value in status['queue']:
                s += "%s<br>" %value
        s+="</td>\n<td id='statuselement'>"
        if not status.get('history', None):
            s+= "&nbsp"
        else:
            for cmd in status['history'].values():
                s += self.resultToHTML(cmd)+'<br>\n'
        s+="</td>\n<td id='statuselement'>"
        if not status.get('engine', None):
            s+= "&nbsp"
        else:
            s+= self.dictToHTML(status['engine'])
        return s+'</td>\n'
    
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
        return s
    
    def dictToHTML(self, d):
        s=''
        if not isinstance(d, dict):
            return str(d)
        for key, value in d.iteritems():
            s += "<b>%s</b> = %s" %(key, value)
            s += '<br>\n'
        return s
        
    def handleOutput(self, result):
        us = self.resultToHTML(result)
        return self.callRemote('handleOutput', us)
    

class ControllerPage(athena.LivePage):
    addSlash = True
    css = open(basedir+'/controllerajaxpb.css').read()
    docFactory = loaders.stan(tags.html[
        tags.head(render=tags.directive('liveglue'))[
                tags.style(type="text/css")[css]
                ],
        tags.body(render=tags.directive('controllerElements'))
        ])
    
    def __init__(self, controller):
        athena.LivePage.__init__(self)
        self.controller = controller
        
    
    def render_style(self, ctx, data):
        f = self.style
        return ctx.tag[f]
    
    def render_controllerElements(self, ctx, data):
        f = ControllerElement(self.controller)
        f.setFragmentParent(self)
        return ctx.tag[f]
        
        g = StatusElement()
        g.setFragmentParent(self)
        return ctx.tag[f, g]
    
class ControllerRoot(object):
    implements(inevow.IResource)
    
    def __init__(self, controller):
        self.controller = controller
    
    def locateChild(self, ctx, segments):
        return ControllerPage(self.controller), segments
    

