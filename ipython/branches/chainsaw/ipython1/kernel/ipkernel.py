from twisted.application import service

from ipython1.kernel.kernelservice import KernelService

application = service.Application('ipkernel')
kes = KernelService(10105)
kes.setServiceParent(application)