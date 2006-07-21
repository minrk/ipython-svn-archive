"""This file contains unittests for the controlllerservice.py module.

Things that should be tested:
- Should the EngineService return Deferred objects?
- Run the same tests that are run in shell.py.
- Make sure that the Interface is really implemented.
- The startService and stopService methods.
"""
import random
import time, exceptions
import cPickle as pickle

from twisted.trial import unittest
from twisted.internet import defer, reactor
from twisted.spread import pb

from ipython1.kernel import engineservice, controllerservice, enginepb, controllerpb
from ipython1.kernel.remoteengine import Command
from ipython1.test.util import DeferredTestCase

import sys
from twisted.python import log

class BasicControllerServiceTest(DeferredTestCase):
    
    def setUp(self):
        #start one controller and connect one engine
        self.services = []
        self.factories = []
        self.clients = []
        self.servers = []
        self.cs = controllerservice.ControllerService()
        self.croot = controllerpb.CRootFromService(self.cs)
        self.eroot = controllerpb.RERootFromService(self.cs)
        self.cf = pb.PBServerFactory(self.croot)
        self.ef = pb.PBServerFactory(self.eroot)
        self.servers.append(reactor.listenTCP(10105, self.cf))
        self.servers.append(reactor.listenTCP(10201, self.ef))
        
        self.es = engineservice.EngineService()
        self.engine = enginepb.PBEngineFromService(self.es)
        f = pb.PBClientFactory()
        client = reactor.connectTCP('127.0.0.1', 10201, f)
        d = self.engine.connect(f)

        self.factories.append(f)
        self.clients.append(client)
        self.services.append(self.es)
        self.services.append(self.cs)
        
        self.cs.startService()
        self.es.startService()
        
        return d
        
    
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
        es2.restart = True
        es2.id = 2
        self.cs.engine[2] = 'restarting'
        dl = defer.DeferredList([d,d2])
        return dl
    
    def testDisconnect(self):
        del self.es
        print 'broken ',
#        self.assertEquals(self.cs.engine, {})
        return
    
    def testPutGet(self):
        l1 = []
        l2 = []
        value = [1.1231232323, (1,'asdf',[2]),'another variable', 
                    [1,2,3,4], {'a':3, 1:'asdf'}]
        key = 'abcde'
        sc = self.cs.submitCommand
        for n in range(0,5):
            d = sc(Command("put", key[n], value[n]))
            l1.append(d)
        dl1 = defer.DeferredList(l1)
        dl1.addCallback(lambda _:defer.DeferredList(
                map(sc,map(Command, ["get"]*len(key), key)))
#        ).addCallback(self.printer)
        ).addCallback(lambda r: map(tuple.__getitem__, r, [1]*len(r))
        ).addCallback(lambda r: map(list.__getitem__, r, [0]*len(r))
        ).addCallback(lambda r: map(tuple.__getitem__, r, [1]*len(r)))
        d = self.assertDeferredEquals(dl1, value)
        return d
    
    def testPutGetPickle(self):
        l1 = []
        l2 = []
        value = [1.1231232323, (1,'asdf',[2]),'another variable', 
                    [1,2,3,4], {'a':3, 1:'asdf'}]
        pValue = map(pickle.dumps, value, [2]*len(value))
        key = 'abcde'
        sc = self.cs.submitCommand
        for n in range(0,5):
            d = sc(Command("putPickle", key[n], pValue[n]))
            l1.append(d)
        dl1 = defer.DeferredList(l1)
#        ).addCallback(self.printer)
        dl1.addCallback(lambda _:defer.DeferredList(
                map(sc,map(Command, ["getPickle"]*len(key), key)))
        ).addCallback(lambda r: map(tuple.__getitem__, r, [1]*len(r))
        ).addCallback(lambda r: map(list.__getitem__, r, [0]*len(r))
        ).addCallback(lambda r: map(tuple.__getitem__, r, [1]*len(r))
        ).addCallback(lambda r: map(pickle.loads, r))
        d = self.assertDeferredEquals(dl1, value)
        return d
    
    #copied from ipython1.test.test_corepb
    def testExecute(self):
        commands = [(0,"a = 5","",""),
            (1,"b = 10","",""),
            (2,"c = a + b","",""),
            (3,"print c","15\n",""),
            (4,"import math","",""),
            (5,"2.0*math.pi","6.2831853071795862\n","")]            
            
        dlist = []
        for id in self.cs.engine.keys():
            if self.cs.engine[id] is not 'restarting':
                d = defer.succeed(None)
                for c in commands:
                    d = self.assertDeferredEquals(self.cs.submitCommand(
                            Command("execute",c[1]), id), c, chainDeferred=d)
                dlist.append(d)
        d = defer.DeferredList(dlist)
        return d
    
    def testScale(self, n=32):#>=124 causes socket.24 too many files error
        dlist = []
        for i in range(1,n):
            (d1, es) = self.newEngine()
            dlist.append(d1)
        d = defer.DeferredList(dlist)
        d.addCallback(lambda _: self.cs.engine.keys())
        d = self.assertDeferredEquals(d, range(n))
        return d
    
    def testScaleExecute(self):
        (d, _) = self.newEngine(16)
        d.addCallback(lambda _:self.testExecute())
        return d
    
    def testScalePutGet(self):
        (d, _) = self.newEngine(16)
        d.addCallback(lambda _:self.testPutGet())
        return d
    
    def testTellAll(self):
        (d, _) = self.newEngine(16)
        sc = self.cs.submitCommand
        d.addCallback(lambda _:sc(Command("put", 'a', 5)))
        return d
    


