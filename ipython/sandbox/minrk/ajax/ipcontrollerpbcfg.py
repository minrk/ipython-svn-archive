from ipython1.kernel.controllervanilla import \
    IVanillaControllerFactory

from ipython1.kernel.controllerpb import \
    IPBControllerFactory

clientVanillaPort = 10105
clientPBPort = 10111

clientInterfaces = [(IVanillaControllerFactory, ('', clientVanillaPort)),
            (IPBControllerFactory, ('', clientPBPort))]
