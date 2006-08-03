from zope.interface import Interface, implements
from twisted.python import components
from twisted.internet import protocol, reactor, defer
from twisted.protocols import basic


from ipython1.kernel.engineservice import EngineService, IEngine, Command
from ipython1.kernel.controllerservice import ControllerService

# Engine side of things

class IVanillaEngineClientProtocol(Interface):
    pass
    
class VanillaEngineClientProtocol(basic.Int32StringReceiver):
    
    implements(IVanillaEngineClientProtocol)

    def connectionMade(self):
        self.transport.setTcpNoDelay(True)
        desiredID = self.factory.getID()
        if desiredID is not None:
            self.sendString("REGISTER %i" % desiredID)
        else:
            self.sendString("REGISTER")
        self.state = 'REGISTERING'

    def stringReceived(self, msg):
        splitLine = msg.split(' ', 1)
        if len(splitLine) == 1:
            cmd = splitLine[0]
            args = None
        else:
            cmd = splitLine[0]
            args = splitLine[1:]
        
        
    # Handlers go here
    
    
    
class IVanillaEngineClientFactory(IEngine):
    
    def getID():
        
    def setID(id):

class VanillaEngineClientFactoryFromEngineService(protocol.ClientFactory):
    
    implements(IVanillaEngineClientFactory)
    
    protocol = VanillaEngineClientProtocol
    
    def __init__(self, service):
        self.service = service
        
    def getID(self):
        return self.service.id
        
    def setID(self, id):
        return self.service.id = id
        
    def execute(self, lines):
        return self.service.execute(lines)
        
    def push(self, **namespace):
        return self.service.push(**namespace)

    def pushPickle(pickledNamespace):
        return self.service.pushPickle(pickledNamespace)

    def pull(*keys):
        return self.service.pull(*keys)

    def pullPickle(*keys):
        return self.service.pullPickle(*keys)

    def getCommand(i=None):
        return self.service.getCommand(i)

    def getLastCommandIndex():
        return self.service.getLastCommandIndex()

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

    
