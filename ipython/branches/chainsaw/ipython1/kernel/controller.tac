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
#try:
from ipython1.kernel.controllerservice import ControllerService
from ipython1.kernel import controllerpb
from ipython1.kernel.remoteengineprocess import RemoteEngineProcessFactory as REPFactory


#init service:
application = service.Application('controller', uid=1, gid=1)
serviceCollection = service.IServiceCollection(application)
cf = REPFactory()
cs = ControllerService(10105, cf, 10106, cf)#see 2 lines down
ef = pb.PBServerFactory(controllerpb.PerspectiveControllerFromService(cs))
cs.remoteEngineFactory = ef #this is just because ef needs cs to exist for its pb constructor

cs.setServiceParent(serviceCollection)

#internet.TCPServer(10105, cs.factory_list[0]
#                  ).setServiceParent(serviceCollection)
#internet.TCPServer(10201, cs.factory_list[1]
#                   ).setServiceParent(serviceCollection)
