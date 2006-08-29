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

def statusListToHTML(statusList, pending, queue, history, local):
    s = "<table id='statusTable'><tr><td><b>id</b>"
    for e in ['pending', 'queue', 'history', 'local']:
        if locals()[e]:
            s+= "<td><b>%s</b></td>" %e    
    for r in statusList:
        s += "<tr><td valign='top'>%i</td>"%r[0]
        s += statusToHTML(r[1], pending, queue, history, local)
        s += '</tr>'
    return s+'</table>'

def statusToHTML(status, pending, queue, history, local):
    s = ""
    if pending:
        s += "<td  id='statuselement'>"
        if not status.get('pending', None):
            s+= "&nbsp"
        else:
            s += "%s<br>" %status['pending']
        s += "</td>"
    if queue:
        s+="<td id='statuselement'>"
        if not status.get('queue', None):
            s+= "&nbsp"
        else:
            for value in status['queue']:
                s += "%s<br>" %value
        s+="</td>"
    if history:
        s += "<td id='statuselement'>"
        if not status.get('history', None):
            s+= "&nbsp"
        else:
            for cmd in status['history'].values():
                s += resultToHTML(cmd)+'<br>\n'
        s += "</td>"
    if local:
        s+="<td id='statuselement'>"
        if not local or not status.get('engine', None):
            s+= "&nbsp"
        else:
            s+= dictToHTML(status['engine'])
        s+'</td>\n'
    return s

def resultToHTML(cmd):
    s=''
    if isinstance(cmd, Failure):
        s+="Failure"
    else:
        target = cmd[0]
        cmd_num = cmd[1]
        cmd_stdin = cmd[2]
        cmd_stdout = cmd[3][:-1]
        cmd_stderr = cmd[4][:-1]
        for c in [cmd_stdin, cmd_stdout, cmd_stderr]:
            c = c.replace('<', '&lt;').replace('>', '&gt;')
        s += "<a id='stdin'>[%i]In [%i]:</a> %s<br>" % (target, cmd_num, cmd_stdin)
        if cmd_stdout:
            s += "<a id='stdout'>[%i]Out[%i]:</a> %s<br>" % (target, cmd_num, cmd_stdout)
        if cmd_stderr:
            s += "<a id='stderr'>[%i]Err[%i]:</a><br> %s<br>" % (target, cmd_num, cmd_stderr)
    return s

def dictToHTML(d):
    s=''
    if not isinstance(d, dict):
        return str(d).replace('<', '&lt;').replace('>', '&gt;')
    for key, value in d.iteritems():
        s += "<b>%s</b> = %s" %(key, repr(value).replace('<', '&lt;').replace('>', '&gt;'))
        s += '<br>\n'
    return s


class ResultElement(athena.LiveElement):
    jsClass = u'ControllerModule.ResultWidget'
    ids = 'all'
    docFactory = loaders.stan([tags.div(render=tags.directive('liveElement')),
        tags.div(id="resultOut")])
    
    def __init__(self):
        reactor.callLater(.1, self.callRemote,'getIDs')
    
    def handleResult(self, result):
        if self.ids != 'all' and result[0] not in self.ids:
            return
        s = resultToHTML(result)
        return self.callRemote('handleResult', unicode(s))
    
    def parseTargets(self, targets):
        try:
            return map(int,targets.split(','))
        except ValueError:
            return 'all'
    
    def setIDs(self, ids):
        self.ids = self.parseTargets(ids)
    
    athena.expose(setIDs)

class StatusElement(athena.LiveElement):
    jsClass = u'ControllerModule.StatusWidget'
    
    docFactory = loaders.stan(tags.div(render=tags.directive('liveElement'))[
        tags.table(id="statusWidget")[
            tags.tr[tags.td[tags.form(id="idform",
                action="""javascript:
                var idform = document.getElementById('idform');
                var w = Nevow.Athena.Widget.get(idform);
                w.refreshStatus();
                """)[
                tags.input(id="idfield", type="text", value="all"),
                tags.br,
                tags.input(type="checkbox", id="pending", checked="true",
                    onChange="this.form.submit()")["pending"],
                tags.input(type="checkbox", id="queue", checked="true",
                    onChange="this.form.submit()")["queue"],
                tags.input(type="checkbox", id="history",
                    onChange="this.form.submit()")["history"],
                tags.input(type="checkbox", id="locals",
                    onChange="this.form.submit()")["locals"],tags.br,
                tags.input(type="submit", value="refresh status")
            ]]],
            tags.tr[tags.td[tags.div(id="statusOut")["click refresh status"]]]
        ]
    ])
    
    def __init__(self, controller):
        self.controller = controller
        reactor.callLater(.1, self.callRemote, 'getIDs')
    
    def parseTargets(self, targets):
        if targets == 'all':
            return 'all'
        try:
            return map(int,targets.split(','))
        except ValueError:
            return False
    
    def status(self, targets, pending=True, queue=True, history=True, locals=True):
        args = (pending, queue, history, locals)
        idlist = self.parseTargets(targets)
        if idlist is False:
            return self.fail()
        d = self.controller.status(idlist)
        return d.addCallbacks(self.statusOK, self.fail, callbackArgs=args)
    
    athena.expose(status)
    
    def statusOK(self, resultList, *args):
        return self.finish(statusListToHTML(resultList, *args))
    
    def refreshStatus(self):
        return self.callRemote('refreshStatus')
    
    def finish(self, s):
        return self.callRemote('updateStatus', unicode(s))
    
    def fail(self, f=None):
        return self.finish('Failure')
    


class CommandElement(athena.LiveElement):
    jsClass = u'ControllerModule.CommandWidget'
    
    docFactory = loaders.stan(tags.div(render=tags.directive('liveElement'))[
        tags.table(id="command", hidden=True)[
        tags.tr[tags.td["cmd"],tags.td["targets"], tags.td["args"]],
        tags.tr[tags.form(id="cmdform",
            action="""javascript:
            var w = Nevow.Athena.Widget.get(document.getElementById('cmdform'));
            var cmd = document.getElementById('cmd');
            cmd = cmd.options[cmd.selectedIndex].value;
            var targets = document.getElementById('targets').value;
            var args = document.getElementById('args').value;
            w.submitCommand(cmd, targets, args);""")[
            
            tags.td[tags.select(id="cmd", name="cmd",
            onchange="Nevow.Athena.Widget.get(this).changeCmd(this.options[cmd.selectedIndex].value);")[
                tags.option(value="execute")["execute"],
                tags.option(value="pull")["pull"],
                tags.option(value="reset")["reset"],
                tags.option(value="kill")["kill"],
            ]],
            tags.td[tags.input(type="text", id="targets", name="targets", value="all")],
            tags.td[tags.input(type="text", id="args", name="args")],
            tags.td[tags.input(type="submit", value="exec")]
        ]],
        tags.tr[tags.td(colspan='4', style="text-align: center")[tags.div(id="commandOut")]]
        ]
    ])
    
    def __init__(self, controller):
        self.controller = controller
        self._notifiers = []
        reactor.callLater(.1, self.callRemote, 'getIDs')
    
    def notify(self):
        for n in self._notifiers:
            n()
    
    def addNotifier(self, n):
        assert callable(n), 'notifiers must be callable'
        self._notifiers.append(n)
    
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
            return self.fail(None)
        d = self.controller.execute(idlist, str(lines))
        self.notify()
        return d.addCallbacks(self.executeOK, self.fail)
    
    athena.expose(execute)
    
    def executeOK(self, resultList):
        s = ''
        for r in resultList:
            s += resultToHTML(r)
        self.finish(unicode(s))
    
    def pull(self, targets, keystr):
        keys = map(str, keystr.split(','))
        idlist = self.parseTargets(targets)
        if not idlist or not keys:
            return self.fail(None)
        d = self.controller.pullNamespace(idlist, *keys)
        self.notify()
        return d.addCallbacks(self.pullOK, self.fail)
    
    athena.expose(pull)
    
    def pullOK(self, resultList):
        s = ''
        print resultList
        for r in resultList:
            s += dictToHTML(r)
        return self.finish(s)
    
    def reset(self, targets, _):
        idlist = self.parseTargets(targets)
        if not idlist:
            return self.fail(None)
        d = self.controller.reset(idlist)
        return d.addCallbacks(self.resetOK, self.fail)
    
    athena.expose(reset)
    
    def resetOK(self, r):
        return self.finish('')
    
    def kill(self, targets, _):
        idlist = self.parseTargets(targets)
        if not idlist:
            return self.fail(None)
        d = self.controller.kill(idlist)
        return d.addCallbacks(self.killOK, self.fail)
    
    athena.expose(kill)
    
    def killOK(self, r):
        return self.finish('')
    
    def finish(self, s):
        self.notify()
        return self.callRemote('commandOutput', unicode(s))
    
    def fail(self, f=None):
        return self.finish('Failure')
    

class ControllerPage(athena.LivePage):
    addSlash = True
    css = open(basedir+'/ajaxpb.css').read()
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
        f = CommandElement(self.controller)
        f.setFragmentParent(self)
        g = StatusElement(self.controller)
        g.setFragmentParent(self)
        h = ResultElement()
        h.setFragmentParent(self)
        self.controller.remote_notify = h.handleResult
        f.addNotifier(g.refreshStatus)
        reactor.callLater(1, g.refreshStatus)
        build = tags.table[
            tags.tr[tags.td(valign="top", rowspan="2")[g], 
                tags.td(valign="top")[h, tags.br, f]]
        ]
        return ctx.tag[build]
    

class ControllerRoot(object):
    implements(inevow.IResource)
    
    def __init__(self, controller):
        self.controller = controller
    
    def locateChild(self, ctx, segments):
        return ControllerPage(self.controller), segments
    

