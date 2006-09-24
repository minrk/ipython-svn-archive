from nevow import athena, loaders, tags, inevow, livepage
from twisted.python import util
from twisted.python.failure import Failure
from twisted.internet import reactor

from ipython1.kernel import results
myPackage = athena.JSPackage({
    'ControllerModule': util.sibpath(__file__, 'athenawidgets.js')
    })

athena.jsDeps.mapping.update(myPackage.mapping)

def classTag(tag, klass):
    if not isinstance(tag, tags.Tag):
        tag = getattr(tags, str(tag))(tmp='tmp')
        del tag.attributes['tmp']
    tag.attributes['class'] = klass
    return tag

def htmlString(s):
    return s.replace('<', '&lt;').replace('>', '&gt;').replace('\n','<br/>')

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
            c = htmlString(c)
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


def parseTargets(targets):
    if targets == 'all':
        return 'all'
    if targets[-1] == ',':
        targets = targets[:-1]
    try:
        return map(int,targets.split(','))
    except ValueError:
        return []


class NotebookWidget(athena.LiveElement):
    jsClass = u'ControllerModule.NotebookWidget'
    docFactory = loaders.stan(tags.div(render=tags.directive('liveElement'))[
    classTag(tags.div, 'pageHeader')["IPython Notebook"],
    classTag(tags.div, 'controlCol')[
        classTag(tags.div(onclick="Nevow.Athena.Widget.get(this).addIOCell();"),
            'controlLink')["Add IO Cell"],
        classTag(tags.div(onclick="Nevow.Athena.Widget.get(this).addTextCell();"),
            'controlLink')["Add Text Cell"],
        classTag(tags.div(onclick="Nevow.Athena.Widget.get(this).createGroup();"),
            'controlLink')["Create Group"],
        tags.hr(size="1"),"Move", tags.br, "Delete",
    ],
    classTag(tags.div(id='nb'), 'notebook')
    ])
    
    def __init__(self, controller):
        self.controller = controller
        reactor.callLater(.1, self.callRemote, 'getIDs')
        reactor.callLater(.1, self.callRemote, 'addIOCell')
        
    def setIDs(self, ids):
        self.ids = parseTargets(ids)
    
    athena.expose(setIDs)
    
    def execute(self, cmd_id, line):
        d = self.controller.execute(self.ids, str(line))
        d.addCallback(self.returnResult, cmd_id)
    
    athena.expose(execute)
    
    def returnResult(self, result, cmd_id):
        print result
        n = len(result)
        if n is 1:
            id = unicode(result[0][1])
            out = htmlString(result[0][3])
            if result[0][4]:
                out += '<br><b>ERR:</b><br>'+htmlString(result[0][4])
        else:
            id = u'*'
            result = map(list, result)
            out = ''
            for i in range(n):
                node = result[i][0]
                # out
                if result[i][3]:
                    out += '%i:%s<br/>'%(node,htmlString(result[i][3]))
                # err
                if result[i][4]:
                    out += '%i:%s<br/>'%(node,htmlString(result[i][4]))
        self.callRemote('handleOutput', cmd_id, id, unicode(out))
    
    
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
            if self.ids == 'all' or result[0] in self.ids:
                return True
    
    def handleResult(self, result):
        if not self.validResult(result):
            return
        s = resultToHTML(result)
        return self.callRemote('handleResult', unicode(s))
    
    def setIDs(self, ids):
        self.ids = parseTargets(ids)
    
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
                tags.input(id="statusidfield", type="text"),
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
            ],tags.div(id="statusOut")
        ]
    ])
    
    def __init__(self, controller):
        self.controller = controller
        reactor.callLater(.1, self.callRemote, 'getIDs')
    
    def status(self, targets, pending=True, queue=True, history=True, locals=True):
        args = (pending, queue, history, locals)
        idlist = parseTargets(targets)
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
        tags.table(id="commandWidget", hidden=True)[
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
            tags.td[tags.input(type="text", id="targets", name="targets")],
            tags.td[tags.input(type="text", id="args", name="args")],
            tags.td[tags.input(type="submit", value="exec")]
        ]],
        tags.tr[tags.td(colspan='4', style="text-align: center;")[tags.div(id="commandOut")]]
        ]
    ])
    
    def __init__(self, controller):
        self.controller = controller
        reactor.callLater(.1, self.callRemote, 'getIDs')
    
    def execute(self, targets, lines):
        idlist = parseTargets(targets)
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
        idlist = parseTargets(targets)
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
        idlist = parseTargets(targets)
        if not idlist:
            return self.fail(None)
        d = self.controller.reset(idlist)
        return d.addCallbacks(self.resetOK, self.fail)
    
    athena.expose(reset)
    
    def resetOK(self, r):
        return self.finish('')
    
    def kill(self, targets, _):
        idlist = parseTargets(targets)
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
        reactor.callLater(1, self.ready)
        n = results.notifierFromFunction(
            lambda _:self.controller.getIDs().addCallback(self.gotIDs))
        self.controller.addNotifier(n)
    
    def ready(self):
        return self.controller.getIDs().addCallback(self.gotIDs)
        
    def gotIDs(self, idlist):
        s = ''
        for id in idlist:
            s += " <a href='monitor?ids=%i')>:%i:</a> " %(id, id)
        return self.callRemote('drawIDs', unicode(s))
    

import time
from nevow.livepage import set, assign, append, js, document, eol
class ChatWidget(athena.LiveElement):
    """This is broken"""
    jsClass = u'ControllerModule.ChatWidget'

    docFactory = loaders.stan([tags.div(render=tags.directive('liveElement'))[
        tags.div(id="topic"), tags.div(id="content")[
            tags.div(pattern="message")[
            classTag(tags.span, 'timestamp')[tags.slot(name='timestamp')],
            classTag(tags.span, 'userid')[tags.slot(name='userid')],
            classTag(tags.span, 'message')[tags.slot(name='message')],
            ]],
            
            tags.dl(id="userlist")[tags.dt["Userlist"],
            tags.dd(pattern="user")[
            # tags.attr(name="id")["user-list-", tags.slot(name="user-id")],
            # tags.slot(name="user-id")
            tags.xml("""
                <nevow:attr name="id">user-list-<nevow:slot name="user-id" /></nevow:attr>
            """),tags.slot(name="user-id")
            ]],
            tags.form(name="inputForm", onsubmit="""
                var w = Nevow.Athena.Widget(this);
                w.callRemote('sendInput', this.inputLine.value);""")[
              tags.input(name="inputLine"),
              tags.input(type="submit", value="say")
            ],
            tags.form(name="nickForm", onsubmit="""
                var w = Nevow.Athena.Widget(this);
                w.callRemote('changeNick', this.nick.value);""")[
              tags.input(name="nick"),
              tags.input(type="submit", value="change nick")
            ],
            tags.form(name="topicForm", onsubmit="""
                var w = Nevow.Athena.Widget(this);
                w.callRemote('changeTopic', this.topic.value);""")[
                tags.input(name="topic"),
                tags.input(type="submit", value="change topic")
            ],
            # tags.span(id="bottom")
    ]])
    messagePattern = inevow.IQ(docFactory).patternGenerator('message')
    userPattern = inevow.IQ(docFactory).patternGenerator('user')
    

    def __init__(self):
        self.clients = []
        self.events = []
    
    def goingLive(self, ctx, client):
        client.notifyOnClose().addBoth(self.userLeft, client)

        client.userId = "newuser"
        client.send(
            assign(document.nickForm.nick.value, client.userId))

        addUserlistEntry = append('userlist', self.userPattern.fillSlots('user-id', client.userId)), eol
        self.sendEvent(
            client, addUserlistEntry, self.content(client, 'has joined.'))

        ## Catch the user up with the previous events
        client.send([(event, eol) for source, event in self.events])

        self.clients.append(client)

    def userLeft(self, _, client):
        self.clients.remove(client)
        self.sendEvent(
            client,
            js.removeNode('user-list-%s' % (client.userId, )), eol,
            self.content(client, 'has left.'))

    def sendEvent(self, source, *event):
        self.events.append((source, event))
        for target in self.clients:
            if target is not source:
                target.send(event)
        return event

    def content(self, sender, message):
        return append(
            'content',
            self.messagePattern.fillSlots(
                'timestamp', time.strftime("%H:%M %d/%m/%y")
            ).fillSlots(
                'userid', sender.userId
            ).fillSlots(
                'message', message)), eol, js.scrollDown()

    def handle_sendInput(self, ctx, inputLine):
        sender = livepage.IClientHandle(ctx)
        return self.sendEvent(sender, self.content(sender, inputLine)), eol, js.focusInput()

    def handle_changeNick(self, ctx, nick):
        changer = livepage.IClientHandle(ctx)
        rv = self.sendEvent(
            changer,
            set('user-list-%s' % (changer.userId, ), nick), eol,
            js.changeId('user-list-%s' % (changer.userId, ), 'user-list-%s' % (nick, )), eol,
            self.content(changer, 'changed nick to %r.' % (nick, )))

        changer.userId = nick
        return rv

    