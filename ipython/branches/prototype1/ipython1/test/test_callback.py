"""This file contains unittests for the callback.py module."""
from twisted.internet import reactor

from ipython1.test.util import DeferredTestCase
from ipython1.startup import callback
from twisted.python import log

class CallbackTest(DeferredTestCase):

    def setUp(self):
        # Parameters
        self.port = 12001
        self.kernel_count = 4
        self.filename = "myfile.txt"
        self.callbackAddr = ('192.168.0.1',10105)
        
        self.startServer()
        d = reactor.callLater(2.0, self.startClients)
        d.callback(reactor.callLaer, s
        # Client
        self.kernelFactories = []
        for k in range(self.kernel_count):
            kf = callback.CallbackClientFactory(self.callbackAddr, tries=2)
            kfConnector = reactor.connectTCP("127.0.0.1", self.port, kf)
            self.kernelFactories.append(kfConnector)
            
        #return d
        
    def startServer(self):
        # Server
        self.callbackFactory = callback.CallbackFactory(self.kernel_count, 
            self.filename)
        self.server = reactor.listenTCP(self.port, self.callbackFactory)        
        
    def tearDown(self):
        for k in self.kernelFactories:
            k.disconnect()

        self.server.stopListening()

        
    def testResult(self):
        self.isNodeFileCorrect()
        #d = reactor.callLater(4.0, self.isNodeFileCorrect)
        #return d
        
    def isNodeFileCorrect(self):
        log.msg("Testing file")
        nodefile = file(self.filename,'r')
        nodes = nodefile.readlines()
        nodefile.close()
        for n in nodes:
            self.assertEqual(n[0].strip(),"192.168.0.1 10105")
        
