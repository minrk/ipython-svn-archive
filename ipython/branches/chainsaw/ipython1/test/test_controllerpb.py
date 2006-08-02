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
        self.reroot = controllerpb.IPBRemoteEngineRoot(self.cs)
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
    
    def testPushPull(self):
        status = {}
        d = self.cs.statusAll()
        d.addCallback(status.update)
        value = [1.1231232323, (1,'asdf',[2]),'another variable', 
                    [1,2,3,4], {'a':3, 1:'asdf'}]
#        value = sys.argv[:8]
        values = tuple(value)
        cnt = len(value)
        key = 'abcdefg'
        key = key
        keys = tuple(key[:cnt])
        namespace = {}
        
        for n in range(cnt):
            namespace[keys[n]] = values[n]
        
        d.addCallback(lambda _:self.cs.push('all', **namespace))
#        d = self.cs.push('all', **namespace)
        d.addCallback(lambda _:self.cs.pull('all', *keys))
        d = self.assertDeferredEquals(d, [values]*len(status))
        return d
    
    def testPushPullPickle(self):
        l1 = []
        l2 = []
        value = [1.1231232323, (1,'asdf',[2]),'another variable', 
                    [1,2,3,4], {'a':3, 1:'asdf'}]
        cnt = len(value)
        #pValue = map(pickle.dumps, value, [2]*cnt)
        key = 'abcdefg'
        keys = tuple(key[:cnt])
        namespace = {}
        
        for n in range(cnt):
            namespace[keys[n]] = value[n]
        
        pickledNamespace = pickle.dumps(namespace, 2)
        d = self.cs.pushPickle(0, pickledNamespace)
        d.addCallback(lambda _:self.cs.pullPickle(0, *keys))
        d.addCallback(lambda pns:pickle.loads(pns[0]))
        d = self.assertDeferredEquals(d, tuple(value))
        return d
    
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
                d = self.assertDeferredEquals(self.cs.execute(id, c[1]), [c], chainDeferred=d)
            dlist.append(d)
        d = defer.DeferredList(dlist)
        return d
    
    def testReset(self):
        d = self.cs.reset(0)
        return d
    
    def testGetLastCommandIndex(self):
        d = self.cs.getLastCommandIndex(0)
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
        d.addCallback(lambda _:self.testPushPull())
        return d
    


