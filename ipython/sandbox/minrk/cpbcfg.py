from ipython1.kernel.enginepb import \
    IPBEngineServerFactory

from ipython1.kernel.controllervanilla import \
    IVanillaControllerFactory

from ipython1.kernel.enginevanilla import \
    IVanillaEngineServerFactory

from ipython1.kernel.controllerpb import \
    IPBControllerFactory

from ipython1.kernel.enginepb import IPBEngineClientFactory


clientPBPort = 10111
clientVanillaPort = 10105

maxMessageSize = 9999

engineClientProtocolInterface = IPBEngineClientFactory

# engineServerProtocolInterface = IVanillaEngineServerFactory
engineServerProtocolInterface = IPBEngineServerFactory

clientInterfaces = [(IVanillaControllerFactory, ('', clientVanillaPort)),
            (IPBControllerFactory, ('', clientPBPort))]
