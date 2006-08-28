from ipython1.kernel.enginepb import \
    IPBEngineServerFactory

from ipython1.kernel.controllervanilla import \
    IVanillaControllerFactory

from ipython1.kernel.controllerpb import \
    IPBControllerFactory

# engineServerProtocolInterface = IVanillaEngineServerFactory
engineServerProtocolInterface = IPBEngineServerFactory

clientInterfaces = [(IVanillaControllerFactory, ('', clientVanillaPort)),
            (IPBControllerFactory, ('', clientPBPort))]
