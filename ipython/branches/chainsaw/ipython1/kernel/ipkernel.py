from twisted.application import service, internet
from twisted.spread import pb

from ipython1.kernel.kernelservice import KernelService, IPerspectiveKernel

application = service.Application('ipkernel')

kes = KernelService(10105)
kes.setServiceParent(application)

pbkes = internet.TCPServer(10106, 
    pb.PBServerFactory(IPerspectiveKernel(kes)))
pbkes.setServiceParent(application)