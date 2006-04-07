from twisted.application import service, internet
from twisted.spread import pb
from twisted.web import server, xmlrpc

from ipython1.kernel import kernelservice, kernelpb, kernelxmlrpc

application = service.Application('ipkernel')

ks = kernelservice.KernelService(10105)
ks.setServiceParent(application)

kspb = internet.TCPServer(10106, 
    pb.PBServerFactory(kernelpb.IPerspectiveKernel(ks)))
kspb.setServiceParent(application)

kssite = server.Site(kernelxmlrpc.IXMLRPCKernel(ks))
ksxr = internet.TCPServer(10104, kssite)
ksxr.setServiceParent(application)
    

