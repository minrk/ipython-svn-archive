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

from ipython1.kernel import engineservice, controllerservice, enginepb
from ipython1.kernel import controllerpb, controllerclient, controller

from ipython1.test.util import DeferredTestCase

import sys
from twisted.python import log
log.startLogging(sys.stdout)

class BasicControllerServiceTest(DeferredTestCase):
    
    def setUp(self):
        #start one controller and connect one engine
        self.services = []
        self.factories = []
        self.clients = []
        self.servers = []
        
        self.cs = controllerservice.ControllerService()
        self.reroot = controllerpb.IPBRemoteEngineRoot(self.cs)
        self.cf = controller.IControlFactory(self.cs)
        self.ref = pb.PBServerFactory(self.reroot)
        
        self.servers.append(reactor.listenTCP(10105, self.cf))
        self.servers.append(reactor.listenTCP(10201, self.ref))
        self.services.append(self.cs)
        
        self.rc = controllerclient.RemoteController(('127.0.0.1', 10105))
        self.rc.block = True
        self.cs.startService()
#        self.rc.connect()
#        return self.newEngine()
    
    def tearDown(self):
        l = []
        del self.rc
        for c in self.clients:
            c.disconnect()
            del c
        for s in self.servers:
            try:
                d = s.stopListening()
                if d is not None:
                    l.append(d)
            except:
                pass
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
        return d
    
    def printer(self, p):
        print p
        return p
    
    def testPushPull(self):
        print 'a'
        self.rc.execute('b=2', block=True)
        print 'b'    

