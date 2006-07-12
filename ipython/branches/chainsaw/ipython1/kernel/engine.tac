"""Engine Application for Twisted Daemon (twistd)
"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from twisted.application import internet, service

from ipython1.kernel.engineservice import EngineService
from ipython1.kernel.controller import EngineFactory

#init service:
es = EngineService()
es.add_f(EngineFactory())

application = service.Application('engine', uid=1, gid=1)
serviceCollection = service.IServiceCollection(application)

cs.setServiceParent(serviceCollection)
internet.TCPClient(10201, es.factory_list[0]
			).setServiceParent(serviceCollection)