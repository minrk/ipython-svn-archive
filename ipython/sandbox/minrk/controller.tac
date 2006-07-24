"""Controller Application for Twisted Daemon (twistd)
"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from twisted.application import internet, service
from twisted.spread import pb
from twisted.internet import reactor

from ipython1.kernel.controllerservice import ControllerService
from ipython1.kernel import controllerpb


#init service:
application = service.Application('controller', uid=1, gid=1)
serviceCollection = service.IServiceCollection(application)

cs = ControllerService()
croot = controllerpb.CRootFromService(cs)
eroot = controllerpb.RERootFromService(cs)

cf = pb.PBServerFactory(croot)
ef = pb.PBServerFactory(eroot)
reactor.listenTCP(10105, cf)
reactor.listenTCP(10201, ef)

cs.setServiceParent(serviceCollection)


#internet.TCPServer(10105, cs.factory_list[0]
#                  ).setServiceParent(serviceCollection)
#internet.TCPServer(10201, cs.factory_list[1]
#                   ).setServiceParent(serviceCollection)
