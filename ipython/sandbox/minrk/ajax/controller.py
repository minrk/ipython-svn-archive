import os
from zope.interface import Interface
from twisted.python.components import registerAdapter
from nevow import athena, inevow, loaders, util
from ipython1.kernel.controllerclient import RemoteController
from ipython1.kernel.controllerservice import IMultiEngine
class IController(Interface):
    def buttonClicked(button):
        pass
    

class Controller(object):
    def __init__(self):
        self.rc = RemoteController(('127.0.0.1', 10105))
        self.rc.connect()
    
    def statusTupleToHTML(self, status):
        s = '<tr><td>%i</td>'%status[0]
        for value in status[1].values():
            s+="<td>"
            if isinstance(value, dict):
                value = value.values()
            for entry in value:
                s+= str(entry)+'<br>'
            s+="</td>"
            print s
        return s+'</tr>\n'
        
    def statusAll(self):
        s = "<div align=\"center\"><table border=\"2\"><tr><td><b>id</b></td><td><b>queue</b></td><td><b>history</b></td></tr>\n"
        for t in self.rc.statusAll():
            s += self.statusTupleToHTML(t)
        
        return unicode(s+'</table></div>')
    
class ControllerResource(athena.LivePage):
    """
    A "live" controller.

    All buttons presses in the browser are sent to the server. The server
    evaluates the expression and sets the output in the browser.
    """
    addSlash = True
    html = os.path.abspath(os.path.curdir)+'/controller.html'
    docFactory = loaders.xmlfile(html)
    print util.resource_filename('ajax', 'controller.html')
    print html

if __name__ == '__main__':

    import sys
    from twisted.internet import reactor
    from twisted.python import log
    from nevow import appserver

    def controllerResourceFactory(original):
        return ControllerResource(IMultiEngine, original)

    registerAdapter(controllerResourceFactory, Controller, inevow.IResource)

    log.startLogging(sys.stdout)
    controller = Controller()
    site = appserver.NevowSite(controller)
    reactor.listenTCP(8080, site)
    reactor.run()
