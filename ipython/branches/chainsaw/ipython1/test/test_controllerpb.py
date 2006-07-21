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
from twisted.internet import defer
from twisted.spread import pb

from ipython1.kernel import engineservice, controllerservice, enginepb, controllerpb
from ipython1.kernel.remoteengine import Command
from ipython1.test.util import DeferredTestCase

#import sys
#from twisted.python import log
#log.startLogging(sys.stdout)

class BasicControllerServiceTest(DeferredTestCase):
    
    def setUp(self):
        #start one controller and connect one engine
        self.services = []
        self.factories = []
        self.cs = controllerservice.ControllerService()
        self.croot = controllerpb.ControlRoot(self.cs)
        self.eroot = controllerpb.RemoteEngineRoot(self.cs)
        self.cf = pb.PBServerFactory(self.croot)
        self.ef = pb.PBServerFactory(self.eroot)
        self.cs.setupControlFactory(10105, self.cf)
        self.cs.setupRemoteEngineFactory(10201, self.ef)
        
        self.f = pb.PBClientFactory()
        self.es = engineservice.EngineService('localhost', 10201, self.f)
        self.engine = enginepb.PerspectiveEngine(self.es)
        
        self.services.append(self.es)
        self.services.append(self.cs)
        
        self.cs.startService()
        
        return self.es.startService()
    
    def tearDown(self):
        l = []
        for s in self.services:
            try:
                d = s.stopService()
                if d is not None:
                    l.append(d)
            except:
                pass
        dl = defer.DeferredList(l)
        return dl
    
    def newEngine(self):
        f = pb.PBClientFactory()
        self.factories.append(f)
        es = engineservice.EngineService('localhost', 10201, f)
        self.services.append(es)
        engine = enginepb.PerspectiveEngine(es)
        d = es.startService()
        return (d,es)
    
    def printer(self, p):
        print p
    
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
                map(sc,map(Command, ["get"]*len(key), key))))
        dl1.addCallback(lambda r: map(tuple.__getitem__, r, [1]*len(r)))
        dl1.addCallback(lambda r: map(list.__getitem__, r, [0]*len(r)))
        dl1.addCallback(lambda r: map(tuple.__getitem__, r, [1]*len(r)))
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
        dl1.addCallback(lambda _:defer.DeferredList(
                map(sc,map(Command, ["getPickle"]*len(key), key))))
        dl1.addCallback(lambda r: map(tuple.__getitem__, r, [1]*len(r)))
        dl1.addCallback(lambda r: map(list.__getitem__, r, [0]*len(r)))
        dl1.addCallback(lambda r: map(tuple.__getitem__, r, [1]*len(r)))
        dl1.addCallback(lambda r: map(pickle.loads, r))
        d = self.assertDeferredEquals(dl1, value)
        return d
    #copied from ipython1.test.test_corepb
    def testExecute(self):
        return
        commands = [(0,"a = 5","",""),
            (1,"b = 10","",""),
            (2,"c = a + b","",""),
            (3,"print c","15\n",""),
            (4,"import math","",""),
            (5,"2.0*math.pi","6.2831853071795862\n","")]            

        dlist = []
        for id in self.cs.engine.keys():
            if self.cs.engine[id] not in [None, 'restarting']:
                d = None
                for c in commands:
                    d = self.assertDeferredEquals(self.cs.submitCommand(
                            Command("execute",c[1]), id), c, chainDeferred=d)
                dlist.append(d)
        d = defer.DeferredList(dlist)
        return d
    
    def testScale(self, n=96):#123 is max, >=124 causes socket too many files error
        dlist = []
        for i in range(1,n):
            (d1, es) = self.newEngine()
            dlist.append(d1)
        d = defer.DeferredList(dlist)
        d.addCallback(lambda _: self.cs.engine.keys())
        d = self.assertDeferredEquals(d, range(n))
        return d
    
#    def testScalePutGet(self):
#        d = self.testScale(2)
#        d.addCallback(lambda _:self.testPutGet())
#        return d
    
