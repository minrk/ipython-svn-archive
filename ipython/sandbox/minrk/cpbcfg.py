from ipython1.kernel.enginepb import \
    IPBEngineServerFactory

from ipython1.kernel.controllervanilla import \
    IVanillaControllerFactory

from ipython1.kernel.enginevanilla import \
    IVanillaEngineServerFactory

from ipython1.kernel.controllerpb import \
    IPBControllerFactory

clientPBPort = 10111
clientVanillaPort = 10105

# engineServerProtocolInterface = IVanillaEngineServerFactory
engineServerProtocolInterface = IPBEngineServerFactory

clientInterfaces = [(IVanillaControllerFactory, ('', clientVanillaPort)),
            (IPBControllerFactory, ('', clientPBPort))]
