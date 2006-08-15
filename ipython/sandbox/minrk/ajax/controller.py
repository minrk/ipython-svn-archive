import os
from zope.interface import Interface
from twisted.python.components import registerAdapter
from nevow import athena, inevow, loaders, util
from twisted.python.failure import Failure
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
        s+="<td>"
        for value in status[1]['queue']:
            s += "%s<br>" %value
        s+="</td>\n<td>"
        for cmd in status[1]['history'].values():
            if isinstance(cmd, Failure):
                s+="Failure"
            else:
                target = cmd[0]
                cmd_num = cmd[1]
                cmd_stdin = cmd[2]
                cmd_stdout = cmd[3][:-1]
                cmd_stderr = cmd[4][:-1]
                s += "<a id='stdin'>In [%i]:</a> %s<br>" % (cmd_num, cmd_stdin)
                if cmd_stdout:
                    s += "<a id='stdout'>Out[%i]:</a> %s<br>" % (cmd_num, cmd_stdout)
                if cmd_stderr:
                    s += "<a id='stderr'>Err[%i]:</a><br> %s<br>" % (cmd_num, cmd_stderr)
            s += '<br>\n'
        s+="</td>"
        return s+'</tr>\n'
        
    def status(self, ids):
        print ids
        s = "<table id='status' border='1'><tr><td><b>id</b></td><td><b>queue</b></td><td><b>history</b></td></tr>\n"
        if ids == 'all':
            stat = self.rc.statusAll()
        else:
            try:
                idlist = map(int,ids.split(','))
                if len(idlist) is 1:
                    id = idlist[0]
                    stat1 = self.rc.status(id)
                    if stat1 is False:
                        return unicode('id %i not registered' %id)
                    stat = [(id, stat1)]
                else:
                    stat = self.rc.status(idlist)
                if stat is False:
                    return unicode('illegal id list: %s' %idlist)
            except ValueError:
                return unicode('illegal id string: %s' %ids)
        for t in stat:
            s += self.statusTupleToHTML(t)
        
        return unicode(s+'</table>')
    
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
