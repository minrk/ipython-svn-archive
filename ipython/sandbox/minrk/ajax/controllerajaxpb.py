from nevow import athena, loaders, tags, inevow, rend
from twisted.internet import reactor
from twisted.python import util
from zope.interface import implements

from ipython1.kernel import results

from widgets import CommandWidget, ResultWidget, StatusWidget

class filePage(rend.Page):
    def __init__(self, *files):
        s = ""
        for f in files:
            s += open(f).read()+'\n'
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
        build = tags.table[
            tags.tr[tags.td(valign="top", rowspan="2")[g], 
                tags.td(valign="top")[h, tags.br, f]]
        ]
        return ctx.tag[build]
    

class MonitorRoot(object):
    implements(inevow.IResource)
    
    def __init__(self, controller):
        self.controller = controller
    
    def locateChild(self, ctx, segments):
        return MonitorPage(self.controller), segments
    

