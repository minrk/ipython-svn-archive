"""This file contains time tests for the controlllerservice.py module.
testing execution times for 16*n for n = 1...7
"""
import time

from twisted.internet import defer, reactor
from twisted.spread import pb

from ipython1.kernel import engineservice, controllerservice, enginepb, controllerpb
from ipython1.kernel.remoteengine import Command
from ipython1.test.util import DeferredTestCase

import sys
from twisted.python import log
#log.startLogging(sys.stdout)

class ControllerTimerTest(DeferredTestCase):
    
    def setUp(self):
        
        self.servers = []
        self.clients = []
        self.cs = controllerservice.ControllerService()
        self.croot = controllerpb.CRootFromService(self.cs)
        self.eroot = controllerpb.RERootFromService(self.cs)
        self.cf = pb.PBServerFactory(self.croot)
        self.ef = pb.PBServerFactory(self.eroot)
        
        self.servers.append(reactor.listenTCP(10105, self.cf))
        self.servers.append(reactor.listenTCP(10201, self.ef))
        
        self.services = [self.cs]
        self.factories = [self.cf, self.ef]
        self.cs.startService()
    
    def tearDown(self):
        l = []
        for s in self.servers:
            try:
                d = s.stopListening()
                if d is not None:
                    l.append(d)
            except:
                pass
        for c in self.clients:
            c.disconnect()
            del c
        dl = defer.DeferredList(l)
        return dl
    
    def newEngine(self, n=1):
        dl = []
        for i in range(n):
            es = engineservice.EngineService()
            engine = enginepb.PBEngineFromService(es)
            f = pb.PBClientFactory()
            client = reactor.connectTCP('localhost', 10201, f)
            d = engine.connect(f)
            es.startService()
            
            self.clients.append(client)
            self.factories.append(f)
            self.services.append(es)

            dl.append(d)
        if n is not 1:
            d = defer.DeferredList(dl)
        return d
    
    def printTime(self, t):
        print "%3.0fms " %(t*1000),
    
    def execute(self, i=0):
        commands = [(0,"a = 5","",""),
            (1,"b = 10","",""),
            (2,"c = a + b","",""),
            (3,"print c","15\n",""),
            (4,"import math","",""),
            (5,"2.0*math.pi","6.2831853071795862\n","")]
        
        c = commands[i]
        dlist = []
        start = time.time()
        for e in self.cs.engine.values():
            d = e.submitCommand(Command("execute",c[1]))
            dlist.append(d)
        dl = defer.DeferredList(dlist)
        dl.addCallback(lambda _:time.time()-start).addCallback(self.printTime)
        return dl
    
    def test001(self):
        d = self.newEngine(1)
        for i in range(6):
            d.addCallback(lambda _:self.execute(i))
        return d
    
    def test016(self):
        d = self.newEngine(16)
        for i in range(6):
            d.addCallback(lambda _:self.execute(i))
        return d
    
    def test032(self):
        d = self.newEngine(32)
        for i in range(6):
            d.addCallback(lambda _:self.execute(i))
        return d
    
    def test048(self):
        d = self.newEngine(48)
        for i in range(6):
            d.addCallback(lambda _:self.execute(i))
        return d
    
    def test064(self):
        d = self.newEngine(64)
        for i in range(6):
            d.addCallback(lambda _:self.execute(i))
        return d

    def test080(self):
        d = self.newEngine(80)
        for i in range(6):
            d.addCallback(lambda _:self.execute(i))
        return d

    def test096(self):
        d = self.newEngine(96)
        for i in range(6):
            d.addCallback(lambda _:self.execute(i))
        return d

    def test112(self):
        d = self.newEngine(123)
        for i in range(6):
            d.addCallback(lambda _:self.execute(i))
        return d
