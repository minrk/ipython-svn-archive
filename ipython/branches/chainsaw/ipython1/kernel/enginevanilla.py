from zope.interface import Interface, implements
from twisted.python import components

from ipython1.kernel.engineservice import EngineService, IEngine, Command
from ipython1.kernel.controllerservice import ControllerService

"""We need

- protocol class
- EngineService -> Client Factory Adapter
- ControllerService -> Server Factory Adaptor
- Server Factory -> IEngine adaptor"""


# Engine side of things

class IVanillaEngineClientProtocol(Interface):
    
class VanillaEngineClientProtocol():
    
    implements(IVanillaEngineClientProtocol)

class IVanillaEngineClientFactory(Interface):
    """This is what the server factory should look like"""

class VanillaEngineClientFactoryFromEngineService():
    pass
    
components.registerAdapter(VanillaEngineClientFactoryFromEngineService,
                           EngineService,
                           IVanillaEngineClientFactory)

    
# Controller side of things

class IVanillaEngineServerProtocol(Interface):
    
class VanillaEngineServerProtocol():
    
    implements(IVanillaEngineServerProtocol)

class IVanillaEngineServerFactory(Interface):
    """This is what the client factory should look like"""

class VanillaEngineServerFactoryFromControllerService():
    pass
    
components.registerAdapter(VanillaEngineServerFactoryFromControllerService,
                           ControllerService,
                           IVanillaEngineServerFactory)
    
class EngineFromVanillaEngineServerProtocol():
    pass
    
components.registerAdapter(EngineFromVanillaEngineServerProtocol,
                           VanillaEngineServerProtocol,
                           IEngine)

    
