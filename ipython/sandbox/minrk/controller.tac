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
from twisted.internet.protocol import Factory

from ipython1.kernel.controllerservice import ControllerService
from ipython1.kernel import controllerpb

#from ipython1.kernel.remoteengineprocess import RemoteEngineProcessFactory as REPFactory


#init service:
application = service.Application('controller', uid=1, gid=1)
serviceCollection = service.IServiceCollection(application)
#the following is convoluted because cs init needs cf,ef which need root which needs cs
f = Factory()
cs = ControllerService(10105, f, 10106, f)
root = controllerpb.PerspectiveControllerFromService(cs)
cf = pb.PBServerFactory(root)
ef = pb.PBServerFactory(root)
cs.__init__(10105, cf, 10106, ef)
del f

cs.remoteEngineFactory = ef #this is just because ef needs cs to exist for its pb constructor

cs.setServiceParent(serviceCollection)

#internet.TCPServer(10105, cs.factory_list[0]
#                  ).setServiceParent(serviceCollection)
#internet.TCPServer(10201, cs.factory_list[1]
#                   ).setServiceParent(serviceCollection)
