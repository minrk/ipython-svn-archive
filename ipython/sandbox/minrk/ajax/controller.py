import os
from zope.interface import Interface
from twisted.python.components import registerAdapter
from nevow import athena, inevow, loaders, util
from twisted.python.failure import Failure
from ipython1.kernel.controllerclient import RemoteController
from ipython1.kernel.util import curry
from ipython1.core.shell import InteractiveShell

class IAjaxController(Interface):
    """Interface for Ajax Controller"""
    def local(targets=None, args=None):
        """local"""
    
    def execute(targets=None, args=None):
        """status"""
    
    def push(targets=None, args=None):
        """status"""
    
    def pull(targets=None, args=None):
        """status"""
    
    def pullNamespace(targets=None, args=None):
        """status"""
    
    def status(targets=None, args=None):
        """status"""
    
    def reset(targets=None, args=None):
        """reset"""
    
    def kill(targets=None, args=None):
        """kill"""
    
    def scatter(targets=None, args=None):
        """scatter"""
    
    def gather(targets=None, args=None):
        """gather"""
    
    def globals(targets=None, args=None):
        """globals"""

class Controller(object):
    def __init__(self):
        self.rc = RemoteController(('127.0.0.1', 10105))
        self.rc.connect()
        self.shell = InteractiveShell()
        self.shell.put('rc', self.rc)
        self.setAutoMethods()
    
    def setAutoMethods(self):
        for method in IAjaxController:
            if not getattr(self, method, None):
                setattr(self, method, curry(self.defaultMethod, method))
    
    def defaultMethod(self, name, targets=None, args=None):
        idlist = self.parseTargets(targets)
        if not idlist:
            return unicode("bad targets: "+ targets)
        self.shell.execute("__RETURN = rc.%s(%r, %s)" %(name, idlist, args))
        r = repr(self.shell.get('__RETURN'))
        return unicode(r)
    
    def parseTargets(self, targets):
        if targets == 'all':
            return targets
        try:
            return map(int,targets.split(','))
        except ValueError:
            return False
    
    def statusTupleToHTML(self, status):
        s = '<tr><td>%i</td>'%status[0]
        s+="<td id='status'>"
        if not status[1].get('queue', None):
            s+= "&nbsp"
        else:
            for value in status[1]['queue']:
                s += "%s<br>" %value
        s+="</td>\n<td id='status'>"
        if not status[1].get('history', None):
            s+= "&nbsp"
        else:
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
        s+="</td>\n<td id='status'>"
        if not status[1].get('engine', None):
            s+= "&nbsp"
        else:
            for key, value in status[1]['engine'].iteritems():
                s += "%s = %s" %(key, value
                )
                s += '<br>\n'
        s+="</td>"
        return s+'</tr>\n'
    
    def status(self, targets=None, args=None):
        idlist = self.parseTargets(targets)
        if not idlist:
            return unicode("bad targets: "+ targets)
        s = "<table><tr><td><b>id</b></td>\
        <td><b>queue</b></td><td><b>history</b></td><td><b>locals</b></td></tr>\n"
        if targets == 'all':
            stat = self.rc.statusAll()
        else:
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
        for t in stat:
            s += self.statusTupleToHTML(t)
        return unicode(s+'</table>')
    
    def local(self, targets=None, args=None):
        try:
            self.shell.execute(args)
        except:
            return unicode("fail")
        return self.globals()
    
    def globals(self, targets=None, args=None):
        dikt = {}
        for k,v in self.shell.locals.iteritems():
            if k not in ['__name__', '__doc__', '__console__', '__builtins__', '__RETURN']:
                dikt[k] = str(v) # want representation, not actual object
        return unicode(dikt)
    
    

class ControllerResource(athena.LivePage):
    """
    A "live" controller.

    All buttons presses in the browser are sent to the server. The server
    evaluates the expression and sets the output in the browser.
    """
    addSlash = True
    html = os.path.abspath(os.path.curdir)+'/controller.html'
    docFactory = loaders.xmlfile(html)

if __name__ == '__main__':

    import sys
    from twisted.internet import reactor
    from twisted.python import log
    from nevow import appserver

    def controllerResourceFactory(original):
        return ControllerResource(IAjaxController, original)

    registerAdapter(controllerResourceFactory, Controller, inevow.IResource)

    log.startLogging(sys.stdout)
    controller = Controller()
    site = appserver.NevowSite(controller)
    reactor.listenTCP(8080, site)
    reactor.run()
