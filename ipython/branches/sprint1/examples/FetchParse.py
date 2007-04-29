"""
An exceptionally lousy site spider
Ken Kinder <ken@kenkinder.com>
"""
from twisted.python.failure import Failure
import ipython1.kernel.api as kernel
import ipython1.kernel.multienginexmlrpc
import ipython1.kernel.taskxmlrpc

try:
    import readline
except ImportError:
    pass

fetchParse = """
from twisted.web import microdom
import urllib2
import urlparse

def fetchAndParse(url, data=None):
    doc = microdom.parseString(urllib2.urlopen(url, data=data).read(), beExtremelyLenient=True)
    links = []
    for node in doc.getElementsByTagName('a'):
        if node.getAttribute('href'):
            links.append(urlparse.urljoin(url, node.getAttribute('href')))
    return links
"""

class DistributedSpider(object):
    def __init__(self, site):
        self.rc = kernel.TaskController(('127.0.0.1', 10113))
        self.ipc = kernel.RemoteController(('127.0.0.1', 10105))
        assert isinstance(self.rc, ipython1.kernel.taskxmlrpc.XMLRPCInteractiveTaskClient)
        assert isinstance(self.ipc, ipython1.kernel.multienginexmlrpc.XMLRPCInteractiveMultiEngineClient)
        self.ipc.execute('all', fetchParse)
        
        self.allLinks = []
        
        self.linksWorking = {}
        self.linksDone = {}
        
        self.site = site
        
    def visitLink(self, url):
        if url not in self.allLinks:
            self.allLinks.append(url)
            if url.startswith(self.site):
                print '    ', url
                self.linksWorking[url] = self.rc.run(kernel.Task('links = fetchAndParse(url)', resultNames=['links'], setupNS={'url': url}))
        
    def onVisitDone(self, result, url):
        print url, ':'
        self.linksDone[url] = None
        del self.linksWorking[url]
        if isinstance(result, Failure):
            txt = result.getTraceback()
            for line in txt.split('\n'):
                print '    ', line
        else:
            for link in result['links']:
                self.visitLink(link)
                
    def run(self):
        self.visitLink(self.site)
        while self.linksWorking:
            print len(self.linksWorking), 'pending...'
            self.synchronize()
    
    def synchronize(self):
        for url, taskId in self.linksWorking.items():
            self.onVisitDone(self.rc.getTaskResult(taskId, block=True)[1], url)

distributedSpider = DistributedSpider(raw_input('Enter site to crawl:'))
distributedSpider.run()
