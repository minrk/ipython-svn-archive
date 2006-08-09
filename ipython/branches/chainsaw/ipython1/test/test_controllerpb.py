"""This file contains unittests for the controlllerservice.py module.

Things that should be tested:
The methods of Controller Service:
    registerEngine √
    unregisterEngine √
    execute/All √o
    push/Serial/All √/√/oo
    pull/Serial/All √/√/oo
    getResult/All √/o
    status/All oo
    reset/All oo
    *kill/All - do not test this, it calls reactor.stop

"""
import random
import time, exceptions
import cPickle as pickle

from twisted.trial import unittest
from twisted.internet import defer, reactor
from twisted.spread import pb

from ipython1.kernel import engineservice, controllerservice, enginepb, enginepb
from ipython1.kernel.engineservice import Command
from ipython1.test.util import DeferredTestCase

import sys
from twisted.python import log
#log.startLogging(sys.stdout)

class BasicControllerServiceTest(DeferredTestCase):
    
    def setUp(self):
        #start one controller and connect one engine
        self.services = []
        self.factories = []
        self.clients = []
        self.servers = []
        self.cs = controllerservice.ControllerService()
        self.reroot = enginepb.IPBRemoteEngineRoot(self.cs)
        self.ref = pb.PBServerFactory(self.reroot)
        self.servers.append(reactor.listenTCP(10201, self.ref))
        
        self.es = engineservice.EngineService()
        ef = enginepb.PBEngineClientFactory(self.es)
        client = reactor.connectTCP('127.0.0.1', 10201, ef)

        self.factories.append(ef)
        self.clients.append(client)
        self.services.append(self.es)
        self.services.append(self.cs)
        
        self.cs.startService()
        self.es.startService()
        
        return ef.deferred
        
    
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
            f = enginepb.PBEngineClientFactory(es)
            client = reactor.connectTCP('localhost', 10201, f)
            d = f.deferred

            es.startService()
            
            self.clients.append(client)
            self.factories.append(f)
            self.services.append(es)

            dl.append(d)
        if n is not 1:
            es = self.services[-n:]
            d = defer.DeferredList(dl)
        return (d, es)
    
    def printer(self, p):
        print p
        return p
    
    def testRegistration(self):
        (d1, es) = self.newEngine()
        d = self.assertDeferredEquals(d1, 1)
        (d2, es2) = self.newEngine()
        es2.id = 2
        dl = defer.DeferredList([d,d2])
        return dl
    
    def testPushPullAll(self):
        status = {}
        d = self.cs.statusAll()
        d.addCallback(status.update)
        values = (1.1231232323, (1,'asdf',[2]),'another variable', 
                    [1,2,3,4], {'a':3, 1:'asdf'})
#        value = sys.argv[:8]
        cnt = len(values)
        key = 'abcdefg'
        key = key
        keys = tuple(key[:cnt])
        namespace = {}
        
        for n in range(cnt):
            namespace[keys[n]] = values[n]
        
        d.addCallback(lambda _:self.cs.pushAll(**namespace))
#        d = self.cs.push('all', **namespace)
        d.addCallback(lambda _:self.cs.pullAll(*keys))
        d = self.assertDeferredEquals(d, zip(*([values]*len(status))))
        return d
    
    def testPushPullSerial(self):
        l1 = []
        l2 = []
        value = [1.1231232323, (1,'asdf',[2]),'another variable', 
                    [1,2,3,4], {'a':3, 1:'asdf'}]
        cnt = len(value)
        key = 'abcdefg'
        keys = tuple(key[:cnt])
        namespace = {}
        
        for n in range(cnt):
            namespace[keys[n]] = value[n]
        
        d = self.cs.pushSerialized(0, **namespace)
        d.addCallback(lambda _:self.cs.pullSerialized(0, *keys))
        d.addCallback(lambda serials: self.nmap(map(getattr, serials, ['unpack']*cnt)))
        d = self.assertDeferredEquals(d, value)
        return d
    
    def nmap(self, flist):
        l = []
        for f in flist:
            l.append(f())
        return l
            
    #adapted from ipython1.test.test_corepb
    def testExecute(self):
        commands = [(0,"a = 5","",""),
            (1,"b = 10","",""),
            (2,"c = a + b","",""),
            (3,"print c","15\n",""),
            (4,"import math","",""),
            (5,"2.0*math.pi","6.2831853071795862\n","")]            
            
        dlist = []
        for id in self.cs.engines.keys():
            d = defer.succeed(None)
            for c in commands:
                d = self.assertDeferredEquals(self.cs.execute(id, c[1]), c, chainDeferred=d)
            dlist.append(d)
        d = defer.DeferredList(dlist)
        return d
    
    def testReset(self):
        d = self.cs.reset(0)
        return d
    
    def testScale(self, n=32):
        dlist = []
        for i in range(1,n):
            (d1, es) = self.newEngine()
            dlist.append(d1)
        d = defer.DeferredList(dlist)
        d.addCallback(lambda _: self.cs.engines.keys())
        d = self.assertDeferredEquals(d, range(n))
        return d
    
    def testScaleExecute(self):
        (d, _) = self.newEngine(16)
        d.addCallback(lambda _:self.testExecute())
        return d
    
    def testScalePushPull(self):
        (d, _) = self.newEngine(16)
        d.addCallback(lambda _:self.testPushPullAll())
        return d
    


