from twisted.application import service

from ipython1.kernel.service import KernelEngineService

application = service.Application('ipkernel')
kes = KernelEngineService(10105)
kes.setServiceParent(application)