from nevow import athena, loaders, tags
from twisted.python import util
from twisted.python.failure import Failure
from twisted.internet import reactor

from ipython1.kernel import results, controllerpb

myPackage = athena.JSPackage({
    'ControllerModule': util.sibpath(__file__, 'athenawidgets.js')
    })

athena.jsDeps.mapping.update(myPackage.mapping)

def statusListToHTML(statusList, pending, queue, history, local):
    s = "<table id='statusTable' align='center'><tr><td><b>id</b>"
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


class ResultWidget(athena.LiveElement):
    jsClass = u'ControllerModule.ResultWidget'
    ids = 'all'
    docFactory = loaders.stan([tags.div(render=tags.directive('liveElement'))[
        tags.div(id="resultIdDiv")[tags.input(
        type='text', align = 'center', id="resultIdField", onChange="""
            w = Nevow.Athena.Widget.get(this);
            w.callRemote('setIDs', this.value);""")]],
        tags.div(id="resultOut")])
    
    def __init__(self):
        reactor.callLater(.1, self.callRemote,'getIDs')
    
    def validResult(self, result):
        if isinstance(result, Failure):
            return True
        if isinstance(result, tuple) and len(result) is 5:
            for i in result[:2]:
                if not isinstance(i, int):
                    return False
            for s in result[2:]:
                if not isinstance(s, str):
                    return False
            return True
    
    def handleResult(self, result):
        if not self.validResult(result):
            return
        s = resultToHTML(result)
        return self.callRemote('handleResult', unicode(s))
    
    def parseTargets(self, targets):
        if targets == 'all':
            return 'all'
        if targets[-1] == ',':
            targets = targets[:-1]
        try:
            return map(int,targets.split(','))
        except ValueError:
            return []
    
    def setIDs(self, ids):
        self.ids = self.parseTargets(ids)
    
    athena.expose(setIDs)

class StatusWidget(athena.LiveElement):
    jsClass = u'ControllerModule.StatusWidget'
    
    docFactory = loaders.stan(tags.div(render=tags.directive('liveElement'))[
        tags.div(id="statusWidget")[
            tags.form(id="statusidform",
                action="""javascript:
                var statusidform = document.getElementById('statusidform');
                var w = Nevow.Athena.Widget.get(statusidform);
                w.refreshStatus();
                """)[
                tags.input(id="statusidfield", type="text", value="all"),
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
            ],tags.div(id="statusOut")["click refresh status"]
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
    
    def refreshStatus(self, *args):
        return self.callRemote('refreshStatus')
    
    def finish(self, s):
        return self.callRemote('updateStatus', unicode(s))
    
    def fail(self, f=None):
        return self.finish('Failure')
    


class CommandWidget(athena.LiveElement, results.NotifierParent):
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
        tags.tr[tags.td(colspan='4', style="text-align: center;")[tags.div(id="commandOut")]]
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
    
    def execute(self, targets, lines):
        idlist = self.parseTargets(targets)
        if idlist is False:
            return self.fail(None)
        d = self.controller.execute(idlist, str(lines))
        self.notify(None)
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
        self.notify(None)
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
        self.notify(None)
        return self.callRemote('commandOutput', unicode(s))
    
    def fail(self, f=None):
        return self.finish('Failure')
    


class IDWidget(athena.LiveElement):
    jsClass = u'ControllerModule.IDWidget'
    
    docFactory = loaders.stan([tags.div(render=tags.directive('liveElement'))[
        tags.div(id="idlist")]])
    
    def __init__(self, controller):
        self.controller = controller
        print self.controller.getIDs().addCallback(self.gotIDs)
        n = results.notifierFromFunction(
            lambda _:self.controller.getIDs().addCallback(self.gotIDs))
        self.controller.addNotifier(n)
    
    def gotIDs(self, idlist):
        s = ''
        for id in idlist:
            s += " <a href='monitor?ids=%i')>:%i:</a> " %(id, id)
        return self.callRemote('drawIDs', unicode(s))
    
    
