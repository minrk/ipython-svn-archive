from nevow import athena, loaders, tags, inevow, rend
from twisted.internet import reactor
from twisted.python import util
from zope.interface import implements

from ipython1.kernel import results

from athenawidgets import CommandWidget, ResultWidget, StatusWidget, IDWidget

class filePage(rend.Page):
    def __init__(self, *files):
        s = ""
        for f in files:
            try:
                s += open(f).read()+'\n'
            except:
                pass
        self.docFactory = loaders.stan(s)
    

class MonitorPage(athena.LivePage):
    addSlash = True
    docFactory = loaders.stan(tags.html[
        tags.head(render=tags.directive('liveglue'))[
                tags.link(rel="stylesheet", type="text/css", href="monitor.css")
                ],
        tags.body(render=tags.directive('widgets'))
        ])
    
    def __init__(self, controller):
        athena.LivePage.__init__(self)
        self.controller = controller
        if not self.children:
            self.children = {}
        self.children["monitor.css"] = filePage(util.sibpath(__file__, 'main.css'), 
                util.sibpath(__file__, 'monitor.css'))
    
    def render_widgets(self, ctx, data):
        f = CommandWidget(self.controller)
        f.setFragmentParent(self)
        g = StatusWidget(self.controller)
        g.setFragmentParent(self)
        h = ResultWidget()
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
                tags.link(rel="stylesheet", type="text/css", href="results.css")
                ],
        tags.body(render=tags.directive('widget'))
        ])
    
    def __init__(self, controller):
        athena.LivePage.__init__(self)
        self.controller = controller
        if not self.children:
            self.children = {}
        self.children["results.css"] = filePage(util.sibpath(__file__, 'main.css'), 
                util.sibpath(__file__, 'results.css'))
    
    def render_widget(self, ctx, data):
        w = ResultWidget()
        w.setFragmentParent(self)
        n1 = results.notifierFromFunction(w.handleResult)
        self.controller.addNotifier(n1)
        return ctx.tag[w]
    

class StatusPage(athena.LivePage):
    addSlash = True
    docFactory = loaders.stan(tags.html[
        tags.head(render=tags.directive('liveglue'))[
                tags.link(rel="stylesheet", type="text/css", href="status.css")
                ],
        tags.body(render=tags.directive('widget'))
        ])
    
    def __init__(self, controller):
        athena.LivePage.__init__(self)
        self.controller = controller
        if not self.children:
            self.children = {}
        self.children["status.css"] = filePage(util.sibpath(__file__, 'main.css'), 
                util.sibpath(__file__, 'status.css'))
    
    def render_widget(self, ctx, data):
        w = StatusWidget(self.controller)
        w.setFragmentParent(self)
        reactor.callLater(.1, w.refreshStatus)
        n2 = results.notifierFromFunction(w.refreshStatus)
        self.controller.addNotifier(n2)
        return ctx.tag[w]
    

class CommandPage(athena.LivePage):
    addSlash = True
    docFactory = loaders.stan(tags.html[
        tags.head(render=tags.directive('liveglue'))[
                tags.link(rel="stylesheet", type="text/css", href="command.css")
                ],
        tags.body(render=tags.directive('widget'))
        ])
    
    def __init__(self, controller):
        athena.LivePage.__init__(self)
        self.controller = controller
        if not self.children:
            self.children = {}
        self.children["command.css"] = filePage(util.sibpath(__file__, 'main.css'), 
                util.sibpath(__file__, 'command.css'))
    
    def render_widget(self, ctx, data):
        w = CommandWidget(self.controller)
        w.setFragmentParent(self)
        return ctx.tag[w]
    

class ControllerPage(athena.LivePage):
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
            tags.a(href="monitor")["monitor"]]
        ]
    ])
    
    def __init__(self, controller):
        athena.LivePage.__init__(self)
        self.controller = controller
        if not self.children:
            self.children = {}
        self.children["command.css"] = filePage(util.sibpath(__file__, 'main.css'), 
                util.sibpath(__file__, 'command.css'))
    
    def render_idwidget(self, ctx, data):
        w = IDWidget(self.controller)
        w.setFragmentParent(self)
        return ctx.tag[w]
        
    def child_results(self, ctx):
        return ResultsPage(self.controller)

    def child_status(self, ctx):
        return StatusPage(self.controller)

    def child_command(self, ctx):
        return CommandPage(self.controller)

    def child_monitor(self, ctx):
        return MonitorPage(self.controller)


class PageRoot(object):
    implements(inevow.IResource)
    
    def __init__(self, Page, *args, **kwargs):
        self.Page = Page
        self.args = args
        self.kwargs = kwargs
    
    def locateChild(self, ctx, segments):
        return self.Page(*self.args, **self.kwargs), segments
    

