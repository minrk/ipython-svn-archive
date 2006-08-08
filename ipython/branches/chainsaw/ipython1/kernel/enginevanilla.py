import cPickle as pickle

from zope.interface import Interface, implements
from twisted.python import components
from twisted.internet import protocol, reactor, defer
from twisted.protocols import basic


from ipython1.kernel.engineservice import EngineService, IEngine
from ipython1.kernel.engineservice import Command, NotImplementedEngine
from ipython1.kernel.controllerservice import ControllerService

# Engine side of things

class IVanillaEngineClientProtocol(Interface):
    pass
    
class VanillaEngineClientProtocol(basic.NetStringReceiver):
    
    implements(IVanillaEngineClientProtocol)

    nextHandler = None

    def connectionMade(self):
        self.transport.setTcpNoDelay(True)
        desiredID = self.factory.getID()
        if desiredID is not None:
            self.sendString("REGISTER %i" % desiredID)
        else:
            self.sendString("REGISTER")
        self.nextHandler = self.handleRegister

    def stringReceived(self, msg):
        
        if self.nextHandler is None:
            self.defaultHandler(msg)
        else:
            self.nextHandler(msg)
            
    def dispatch(self, msg):
        # Try to parse out a command
        splitLine = msg.split(' ', 1)
        if len(splitLine) == 1:
            cmd = splitLine[0]
            args = None
        else:
            cmd = splitLine[0]
            args = splitLine[1:]
        
        # Try to dispatch to a handle_READY_COMMAND method
        f = getattr(self, 'handle_%s' %
                    (cmd), None)            
        if f:
            # Handler resolved with state and cmd 
            f(args)
        else:
            self.sendString('BAD COMMAND')
            self._reset()
            
    # Utility methods
            
    def _reset(self):
        self.nextHandler = self.dispatch

    def handleUnexpectedData(self, args):
        self.sendString('UNEXPECTED DATA')

    def sendPickle(self, data, key):
        try:
            package = pickle.dumps(data, 2)
        except pickle.PickleError:
            return defer.fail()
        else:
            self.sendString('PICKLE %s' % key)
            self.sendString(package)
            return defer.succeed(None)
    
    def handleRegister(self, args):
        # args = 'REGISTER id'
        try:
            id = int(args)
        except TypeError:
            raise
        else:
            self.factory.setID(id)
            self._reset()
            
    # EXECUTE
            
    def handle_EXECUTE(self, lines):
        d = self.factory.execute(lines)
        d.addCallback(self.handleExecuteSuccess)
        d.addErrback(self.executeFail)
        self.nextHandler = self.handleUnexpectedData
        
    def handleExecuteSuccess(self, result):
        d = self.sendPickle(result, 'result')
        d.addErrback(self.executeFail)
        d.addCallback(self.executeOK)
 
    def executeOK(self, args):
        self.sendString('EXECUTE OK')
        self._reset()
         
    def executeFail(self, reason):
        self.sendString('EXECUTE FAIL')
        self._reset()
    
    # PUSH
    
    def handle_READY_PUSH(self, args):
        if args is not None:
            self.sendString('BAD COMMAND')
            self._reset()
        else:
            d = self.getIncomingData()
            d.addCallback()
            d.addErrback()
    
    def getIncomingData(self):
        self.nextHandler = self.handleIncomingData
        
        return d
        
    def handleIncomingData(self, data):
        

class IVanillaEngineClientFactory(IEngine):
    
    def getID():
        """Get's the engines id."""
        
    def setID(id):
        """Set's the engines id."""

class VanillaEngineClientFactoryFromEngineService(protocol.ClientFactory,
    NotImplementedEngine):
    
    implements(IVanillaEngineClientFactory)
    
    protocol = VanillaEngineClientProtocol
    
    def __init__(self, service):
        self.service = service
        
    # From IVanillaEngineClientFactory
    def getID(self):
        return self.service.id
        
    def setID(self, id):
        # Add some error checking.
        return self.service.id = id
        
    # From IEngine
    def execute(self, lines):
        return self.service.execute(lines)
        
    def push(self, **namespace):
        return self.service.push(**namespace)

    def pull(self, *keys):
        return self.service.pull(*keys)
        
    def pullNamespace(self, *keys):
        return self.service.pullNamespace(*keys)

    def getResult(self, i=None):
        return self.service.getResult(i)

    def reset():
        return self.service.reset()

    def kill():
        return self.service.kill()

    def status():
        return self.service.status()
        
components.registerAdapter(VanillaEngineClientFactoryFromEngineService,
                           EngineService,
                           IVanillaEngineClientFactory)

    
# Controller side of things

class IVanillaEngineServerProtocol(Interface):
    
class VanillaEngineServerProtocol(basic.Int32StringReceiver):
    
    implements(IVanillaEngineServerProtocol)

class IVanillaEngineServerFactory(Interface):
    """This is what the client factory should look like"""

class VanillaEngineServerFactoryFromControllerService(protocol.ServerFactory):
    
    implements(IVanillaEngineServerFactory)
    
    protocol = VanillaEngineServerProtocol
    
components.registerAdapter(VanillaEngineServerFactoryFromControllerService,
                           ControllerService,
                           IVanillaEngineServerFactory)
    
class EngineFromVanillaEngineServerProtocol():

    implements(IEngine)
    
    
components.registerAdapter(EngineFromVanillaEngineServerProtocol,
                           VanillaEngineServerProtocol,
                           IEngine)

    
