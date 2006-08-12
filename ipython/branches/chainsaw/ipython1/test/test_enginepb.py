"""This file contains unittests for the enginepb.py module.

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

#*****************************************************************************
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from twisted.python import components
from twisted.internet import reactor, defer
from twisted.spread import pb

from ipython1.test import util
from ipython1.test  import completeenginetest as cet
from ipython1.kernel import engineservice as es, enginepb, controllerservice as cs

class EnginePBTest(cet.CompleteEngineTestCase):
#class EnginePBTest(util.DeferredTestCase):
        
    def setUp(self):
        #start one controller and connect one engine
        self.services = []
        self.clients = []
        self.servers = []
        self.sroot = enginepb.PBRemoteEngineRootFromService(self)
        self.sf = pb.PBServerFactory(self.sroot)
        self.servers.append(reactor.listenTCP(10201, self.sf))
        
        self.es = es.EngineService()
        ef = enginepb.PBEngineClientFactory(self.es)
        client = reactor.connectTCP('127.0.0.1', 10201, ef)
        
        self.clients.append(client)
        self.services.append(self.es)
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
    
    def registerEngine(self, remoteEngine, id):
        self.e = remoteEngine
        return id
    
    def unregisterEngine(self, id):
        pass
    
    def registerSerializationTypes(self, *types):
        pass
    
