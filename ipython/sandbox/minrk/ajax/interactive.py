import os
import random
from zope.interface import Interface
from twisted.python.components import registerAdapter
from twisted.python.failure import Failure
from nevow import athena, inevow, loaders, util
from ipython1.core.shell import InteractiveShell

class IAjaxShell(Interface):
    """Interface for Ajax Shell"""
    def execute(lines, id):
        """execute lines in id's shell"""
    
    def getResults():
        """get all results"""
    
    def getNextCommandIndex():
        """get last command index+1"""
    

class AjaxShell(object):
    """Ajax Shell object"""
    
    def __init__(self):
        self.shell = InteractiveShell()
        self.shell.execute("import ipython1.kernel.controllerclient as cc")
        self.shell.execute("rc = cc.RemoteController(('127.0.0.1', 10105))")
    
    def getNextCommandIndex(self):
        return unicode(self.shell.getLastCommandIndex()+1)
    
    def getResults(self):
        n = self.shell.getLastCommandIndex()
        s = ""
        for i in range(n+1):
            s += self.resultTupleToHTML(self.shell.getCommand(i))
        return unicode(s)
    
    def execute(self, lines):
        print 'execute',lines
        self.shell.execute(lines)
        r = unicode(self.resultTupleToHTML(self.shell.getCommand()))
        return r
    
    def resultTupleToHTML(self, cmd):
        s = ""
        if isinstance(cmd, (Failure, Exception)):
            s+="Failure"
        else:
            cmd_num = cmd[0]
            cmd_stdin = cmd[1]
            cmd_stdout = cmd[2][:-1]
            cmd_stderr = cmd[3][:-1]
            s += "<a id='stdin'>In [%i]:</a> %s<br>" % (cmd_num, cmd_stdin)
            if cmd_stdout:
                s += "<a id='stdout'>Out[%i]:</a> %s<br>" % (cmd_num, cmd_stdout)
            if cmd_stderr:
                s += "<a id='stderr'>Err[%i]:</a><br> %s<br>" % (cmd_num, cmd_stderr)
        s += '<br>\n'
        return s
        
    

class AjaxShellResource(athena.LivePage):
    """
    A "live" controller.
    
    All buttons presses in the browser are sent to the server. The server
    evaluates the expression and sets the output in the browser.
    """
    addSlash = True
    html = os.path.abspath(os.path.curdir)+'/interactive.html'
    docFactory = loaders.xmlfile(html)    

if __name__ == '__main__':

    import sys
    from twisted.internet import reactor
    from twisted.python import log
    from nevow import appserver

    def shellResourceFactory(original):
        klass = original.__class__ # a new one for each connection
        return AjaxShellResource(IAjaxShell, klass())
    
    registerAdapter(shellResourceFactory, AjaxShell, inevow.IResource)

    log.startLogging(sys.stdout)
    ashell = AjaxShell()
    site = appserver.NevowSite(ashell)
    reactor.listenTCP(8080, site)
    reactor.run()
    



