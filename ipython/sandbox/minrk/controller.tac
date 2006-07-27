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
from ipython1.kernel import controllerpb, controller


#init service:
application = service.Application('controller', uid=1, gid=1)
serviceCollection = service.IServiceCollection(application)

cs = ControllerService()

reroot = controllerpb.IPBRemoteEngineRoot(cs)
cf = controller.IControlFactory(cs)
ref = pb.PBServerFactory(reroot)

reactor.listenTCP(10101, cf)
reactor.listenTCP(10102, ref)

cs.setServiceParent(serviceCollection)
