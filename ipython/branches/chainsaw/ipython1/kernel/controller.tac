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

from ipython1.kernel.controllerservice import ControllerService
from ipython1.kernel.controller import ControllerFactory
from ipython1.kernel.engineclient import EngineClientFactory

#init service:
cs = controllerservice()
cs.addFactory(ControllerFactory())
cs.addFactory(EngineClientFactory())
application = service.Application('controller', uid=1, gid=1)
serviceCollection = service.IServiceCollection(application)

cs.setServiceParent(serviceCollection)

internet.TCPServer(10105, cs.factoryList[0]
                   ).setServiceParent(serviceCollection)
internet.TCPServer(10201, cs.factoryList[1]
                   ).setServiceParent(serviceCollection)
