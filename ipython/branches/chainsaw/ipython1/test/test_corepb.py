"""This file contains unittests for the corepb.py module.

Things that should be tested:
- The same interface methods that are tested in shell.py and coreservice.pb
- That the Interface is really implemented fully and properly.

It seems like the tests for shell.py, coreservice.py and corepb.py should have
lots of overlap.  This makes it seem like I should have tests that can be run
in different contexts.  Or is this overkill?
"""
from twisted.spread import pb
import twisted.spread.pb
from twisted.internet import reactor

from ipython1.test.util import DeferredTestCase
from ipython1.kernel2p import coreservice, corepb

class CorePBTest(DeferredTestCase):

    def setUp(self):
        self.ipcore = coreservice.CoreService()
        self.ipcore.startService()
        self.portno = 12001
        self.pb_serv_fact = pb.PBServerFactory(corepb.IPerspectiveCore(self.ipcore))
        self.server = reactor.listenTCP(self.portno, self.pb_serv_fact,
                                   interface='127.0.0.1')

        self.pb_client_fact = pb.PBClientFactory()
        reactor.connectTCP("127.0.0.1", self.portno, self.pb_client_fact)
        d = self.pb_client_fact.getRootObject()
        d.addCallback(self.gotRootObject)
        return d
        
    def gotRootObject(self, r):
        self.r = r
        
    def tearDown(self):
        self.ipcore.stopService()
        if self.r:
            self.r.broker.transport.loseConnection()
        return self.server.stopListening()
        
        
    def testExecute(self):
        commands = [(0,"a = 5","",""),
            (1,"b = 10","",""),
            (2,"c = a + b","",""),
            (3,"print c","15\n",""),
            (4,"import math","",""),
            (5,"2.0*math.pi","6.2831853071795862\n","")]
        
        d = self.assertDeferredEquals(self.r.callRemote("execute",commands[0][1]), 
                                      commands[0])
        for c in commands[1:]:
            d = self.assertDeferredEquals(self.r.callRemote("execute",c[1]), 
                                          c, chainDeferred=d)
        return d

    def testPut(self):
        d1 = self.r.callRemote("put",10,10)
        #def fprint(f):
        #    print " .type =", f.type
        #    print " .value =", f.value
        #    print " .tb = ", f.tb
        #    return f
        #d1.addBoth(fprint)
        d = self.assertDeferredRaises(d1, twisted.spread.pb.Error)
        #d = self.assertDeferredEquals(self.r.callRemote("get","a"),10,d)
        #    print "Hi there"
        #d1.addCallback(printer)
        #d2 = self.assertDeferredRaises(d1, TypeError)
        return d
