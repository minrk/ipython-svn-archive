from twisted.application import service, internet
from twisted.spread import pb
from twisted.web import server, xmlrpc

from ipython1.kernel import kernelservice, kernelpb, kernelxmlrpc
from ipython1.bonjour.twistbonjour import PBServerFactoryBonjour

application = service.Application('ipkernel')

ks = kernelservice.KernelService(10105)
ks.setServiceParent(application)

pbfact = PBServerFactoryBonjour(kernelpb.IPerspectiveKernel(ks),
            serviceName="ipkernel", serviceType="_ipython._tcp",
            servicePort=10106)

kspb = internet.TCPServer(10106, pbfact)
kspb.setServiceParent(application)

kssite = server.Site(kernelxmlrpc.IXMLRPCKernel(ks))
ksxr = internet.TCPServer(10104, kssite)
ksxr.setServiceParent(application)
    

