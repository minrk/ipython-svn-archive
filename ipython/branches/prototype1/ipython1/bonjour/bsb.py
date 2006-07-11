#!/usr/bin/env python
"""
This script using NSNetServiceBrowser to look for local HTTP servers.
"""

import objc
from Foundation import *

class PrintingResolverDelegate(NSObject):
    def netServiceDidResolveAddress_(self, service):
        addresses = service.addresses()
        if len(addresses) == 0:
            return
        print "%s.%s" % (service.name(), service.domain())
        for address in service.addresses():
            print "   %s"%(address,)
        print ""

    def netService_didNotResolve_(self, didNotResolve):
        print "didNotResolve",didNotResolve

class PrintingBrowserDelegate(NSObject):
    def startLookup(self):
        for aNetService in self.services:
            prd = PrintingResolverDelegate.new()
            aNetService.setDelegate_(prd)
            aNetService.resolve()

    def netServiceBrowserWillSearch_(self, browser):
        print "Browsing for advertised services..."
        self.services = []

    def netServiceBrowserDidStopSearch_(self, browser):
        print "Browse complete"
        self.startLookup()

    def netServiceBrowser_didNotSearch_(self, browser, errorDict):
        print "Could not search."

    def netServiceBrowser_didFindService_moreComing_(self, browser, aNetService, moreComing):
        print "Found a service: %s %s"%(aNetService.name(), aNetService.domain())
        self.services.append(aNetService)
        if not moreComing:
            browser.stop()

    def netServiceBrowser_didRemoveService_moreComing_(self, browser, aNetService, moreComing):
        print "Service removed: %s"%(aNetService.name(),)
        if not moreComing:
            browser.stop()

def findDomains(serviceName, seconds=5.0):
    runloop = NSRunLoop.currentRunLoop()
    browser = NSNetServiceBrowser.new()
    pbd = PrintingBrowserDelegate.new()
    browser.setDelegate_(pbd)
    browser.searchForServicesOfType_inDomain_(serviceName, u'local.')
    untilWhen = NSDate.dateWithTimeIntervalSinceNow_(seconds)
    runloop.runUntilDate_(untilWhen)

class BonjourServiceBrowser(NSObject):
    def browse(self,serviceName, domain = u'local.',seconds=5.0):
        self.serviceName = unicode(serviceName)
        self.domain = unicode(domain)
        self.addresses = []
        self.runloop = NSRunLoop.currentRunLoop()
        self.browser = NSNetServiceBrowser.new()
        self.browser.setDelegate_(self)
        self.browser.searchForServicesOfType_inDomain_(self.serviceName, self.domain)
        untilWhen = NSDate.dateWithTimeIntervalSinceNow_(seconds)
        self.runloop.runUntilDate_(untilWhen)
        return self.addresses

    def netServiceBrowserWillSearch_(self, browser):
        print u"Browsing for advertised services..."
        self.services = []

    def netServiceBrowserDidStopSearch_(self, browser):
        print u"Browse complete"
        self.startLookup()
        #print self.services
        
    def netServiceBrowser_didNotSearch_(self, browser, errorDict):
        print u"Could not search."
        print errorDict

    def netServiceBrowser_didFindService_moreComing_(self, browser, aNetService, moreComing):
        print u'Found a service: %s %s'%(unicode(aNetService.name()), 
            unicode(aNetService.domain()))
        self.services.append(aNetService)
        if not moreComing:
            browser.stop()

    def netServiceBrowser_didRemoveService_moreComing_(self, browser, aNetService, moreComing):
        print u"Service removed: %s"%(aNetService.name(),)
        if not moreComing:
            browser.stop()

    def startLookup(self):
        for aNetService in self.services:
            prd = PrintingResolverDelegate.new()
            aNetService.setDelegate_(self)
            aNetService.resolve()

    def netServiceDidResolveAddress_(self, service):
        print u"resolving"
        addrs = service.addresses()
        #print service.name(), service.domain(), addrs
        if len(addrs) == 0:
            return
        host = u'%s.%s' % (unicode(service.name()), unicode(service.domain()))
        for a in addrs:
            if len(a) == 2:
                self.addresses.append(a)

    def netService_didNotResolve_(self, didNotResolve):
        print "didNotResolve",didNotResolve


if __name__ == '__main__':
    # Use '_afpovertcp' instead of '_http' to look for fileservers.
    #findDomains("_afpovertcp._tcp")    
    sb = BonjourServiceBrowser.alloc().init()
    #sb.browse('_daap._tcp.', domain=u'local.')
    #for node in iFound:
    #    print node