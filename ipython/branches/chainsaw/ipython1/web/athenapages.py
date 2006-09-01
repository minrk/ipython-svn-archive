from nevow import athena, loaders, tags, inevow, rend, livepage
from twisted.internet import reactor
from twisted.python import util
from zope.interface import implements

from ipython1.kernel import results

from ipython1.web import athenawidgets as aw

class filePage(rend.Page):
    def __init__(self, *files):
        s = ""
        for f in files:
            try:
                s += open(f).read()+'\n'
            except:
                pass
        self.docFactory = loaders.stan(tags.raw(s))
    

class MonitorPage(athena.LivePage):
    addSlash = True
    docFactory = loaders.stan(tags.html[
        tags.head(render=tags.directive('liveglue'))[
                tags.title["IPython Monitor"],
                tags.link(rel="stylesheet", type="text/css", href="monitor.css")
                ],
        tags.body[tags.h1["IPython Monitor"],
            tags.div(render=tags.directive('widgets'))]
        ])
    
    def __init__(self, controller):
        athena.LivePage.__init__(self)
        self.controller = controller
        if not self.children:
            self.children = {}
        self.children["monitor.css"] = filePage(util.sibpath(__file__, 'main.css'), 
                util.sibpath(__file__, 'monitor.css'))
    
    def render_widgets(self, ctx, data):
        f = aw.CommandWidget(self.controller)
        f.setFragmentParent(self)
        g = aw.StatusWidget(self.controller)
        g.setFragmentParent(self)
        h = aw.ResultWidget()
        h.setFragmentParent(self)
        n1 = results.notifierFromFunction(h.handleResult)
        self.controller.addNotifier(n1)
        n2 = results.notifierFromFunction(g.refreshStatus)
        f.addNotifier(n2)
        reactor.callLater(1, g.refreshStatus)
        build = tags.table(id="monitor")[
            tags.tr[tags.td(valign="top")[g], 
                tags.td(valign="top")[h, tags.br, f]]
        ]
        return ctx.tag[build]
    

class ResultsPage(athena.LivePage):
    addSlash = True
    docFactory = loaders.stan(tags.html[
        tags.head(render=tags.directive('liveglue'))[
                tags.title["IPython Results"],
                tags.link(rel="stylesheet", type="text/css", href="results.css")
                ],
        tags.body[tags.h1["IPython Results"],
            tags.div(render=tags.directive('widgets'))]
        ])
    
    def __init__(self, controller):
        athena.LivePage.__init__(self)
        self.controller = controller
        if not self.children:
            self.children = {}
        self.children["results.css"] = filePage(util.sibpath(__file__, 'main.css'), 
                util.sibpath(__file__, 'results.css'))
    
    def render_widgets(self, ctx, data):
        w = aw.ResultWidget()
        w.setFragmentParent(self)
        n1 = results.notifierFromFunction(w.handleResult)
        self.controller.addNotifier(n1)
        c = aw.CommandWidget(self.controller)
        c.setFragmentParent(self)
        return ctx.tag[w,tags.br,c]
    

class StatusPage(athena.LivePage):
    addSlash = True
    docFactory = loaders.stan(tags.html[
        tags.head(render=tags.directive('liveglue'))[
                tags.title["IPython Status"],
                tags.link(rel="stylesheet", type="text/css", href="status.css")
                ],
        tags.body[tags.h1["IPython Status"],
            tags.div(render=tags.directive('widgets'))]
        ])
    
    def __init__(self, controller):
        athena.LivePage.__init__(self)
        self.controller = controller
        if not self.children:
            self.children = {}
        self.children["status.css"] = filePage(util.sibpath(__file__, 'main.css'), 
                util.sibpath(__file__, 'status.css'))
    
    def render_widgets(self, ctx, data):
        w = aw.StatusWidget(self.controller)
        w.setFragmentParent(self)
        reactor.callLater(.1, w.refreshStatus)
        n2 = results.notifierFromFunction(w.refreshStatus)
        self.controller.addNotifier(n2)
        c = aw.CommandWidget(self.controller)
        c.setFragmentParent(self)
        c.addNotifier(n2)
        return ctx.tag[w,tags.br,c]
    

class CommandPage(athena.LivePage):
    addSlash = True
    docFactory = loaders.stan(tags.html[
        tags.head(render=tags.directive('liveglue'))[
                tags.title["IPython Command"],
                tags.link(rel="stylesheet", type="text/css", href="command.css")
                ],
        tags.body[tags.h1["IPython Command"],
            tags.div(render=tags.directive('widget'))]
        ])
    
    def __init__(self, controller):
        athena.LivePage.__init__(self)
        self.controller = controller
        if not self.children:
            self.children = {}
        self.children["command.css"] = filePage(util.sibpath(__file__, 'main.css'), 
                util.sibpath(__file__, 'command.css'))
    
    def render_widget(self, ctx, data):
        w = aw.CommandWidget(self.controller)
        w.setFragmentParent(self)
        return ctx.tag[w]
    

class ControllerPageAthena(athena.LivePage):
    chat=None
    addSlash = True
    docFactory = loaders.stan(tags.html[
        tags.head(render=tags.directive('liveglue'))[
                tags.link(rel="stylesheet", type="text/css",
                href="controller.css")],
        tags.body[tags.h1["IPython Controller"],
            tags.br,
            tags.h2[
            tags.div(render=tags.directive('idwidget')),tags.br,
            tags.a(href="results")["results"],tags.br,
            tags.a(href="status")["status"],tags.br,
            tags.a(href="command")["command"],tags.br,
            tags.a(href="monitor")["monitor"]],tags.br,
            tags.div(render=tags.directive('chat'))
        ]
    ])
    
    def __init__(self, controller):
        athena.LivePage.__init__(self)
        self.controller = controller
        if not self.children:
            self.children = {}
        self.children["controller.css"] = filePage(util.sibpath(__file__, 'main.css'), 
                util.sibpath(__file__, 'controller.css'))
    
    def render_idwidget(self, ctx, data):
        w = aw.IDWidget(self.controller)
        w.setFragmentParent(self)
        return ctx.tag[w]
    
    def render_chat(self, ctx, data):
        self.chat = "NO CHAT"
        if self.chat is None:
            self.chat = aw.ChatWidget()
            self.chat.setFragmentParent(self)
        return ctx.tag[self.chat]
    
    def child_results(self, ctx):
        return ResultsPage(self.controller)
    
    def child_status(self, ctx):
        return StatusPage(self.controller)
    
    def child_command(self, ctx):
        return CommandPage(self.controller)
    
    def child_monitor(self, ctx):
        return MonitorPage(self.controller)
    
    def goingLive(self, ctx, client):
        return self.chat.goingLive(ctx, client)
    



import os, time
from nevow.livepage import set, assign, append, js, document, eol
class ControllerPageLivepage(livepage.LivePage):
    
    addSlash = True
    docFactory = loaders.xmlfile(os.path.join(util.sibpath(__file__, 'controller.html')))
    messagePattern = inevow.IQ(docFactory).patternGenerator('message')
    userPattern = inevow.IQ(docFactory).patternGenerator('user')
    
    def __init__(self, controller):
        livepage.LivePage.__init__(self)
        self.controller = controller
        self.clients = []
        self.events = []
        self.controller.getIDs().addCallback(self.gotIDs)
        n = results.notifierFromFunction(
            lambda _:self.controller.getIDs().addCallback(self.gotIDs))
        self.controller.addNotifier(n)
        
    
    def gotIDs(self, idlist):
        s = ''
        for id in idlist:
            s += " <a href='notebook?ids=%i')>%i</a> " %(id, id)
        self.sendEvent(None, assign(
            document.getElementById('idlist').innerHTML, unicode(s)))
    
    def child_results(self, ctx):
        return ResultsPage(self.controller)

    def child_status(self, ctx):
        return StatusPage(self.controller)
    
    def child_command(self, ctx):
        return CommandPage(self.controller)
    
    def child_monitor(self, ctx):
        return MonitorPage(self.controller)
    
    def child_notebook(self, ctx):
        return NotebookPage(self.controller)
    
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

ControllerPage = ControllerPageLivepage

class NotebookPage(athena.LivePage):
    addSlash=True
    docFactory = loaders.stan(tags.html[tags.head(render=tags.directive('liveglue'))[
        tags.title["IPython Notebook"],
        tags.link(href="notebook.css", rel="stylesheet", type="text/css"),
        # tags.script(type="text/javascript", src="nested.js")
    ],tags.body(render=tags.directive('widget'))
    ])
    def __init__(self, controller):
        athena.LivePage.__init__(self)
        self.controller = controller
        if self.children is None:
            self.children = {}
        self.children["notebook.css"] = filePage(
            util.sibpath(__file__, 'notebook.css'))
    
    def render_widget(self, ctx, data):
        w = aw.NotebookWidget(self.controller)
        w.setFragmentParent(self)
        return ctx.tag[w]
    


class PageRoot(object):
    implements(inevow.IResource)
    
    def __init__(self, Page, *args, **kwargs):
        self.Page = Page
        self.args = args
        self.kwargs = kwargs
    
    def locateChild(self, ctx, segments):
        return self.Page(*self.args, **self.kwargs), segments
    

