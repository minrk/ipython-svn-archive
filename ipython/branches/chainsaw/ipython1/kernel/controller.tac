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
#try:
from ipython1.kernel.controllerservice import ControllerService
from ipython1.kernel.remoteengineprocess import RemoteEngineProcessFactory as REPFactory
#	from ipython1.kernel.engineclient import EngineClientFactory
#except ImportError:
#    print "ipython1 needs to be in your PYTHONPATH"


#init service:
application = service.Application('controller', uid=1, gid=1)
serviceCollection = service.IServiceCollection(application)

f = REPFactory()
f2 = REPFactory()
cs = ControllerService(10105, f, 10106, f2)

cs.setServiceParent(serviceCollection)

#internet.TCPServer(10105, cs.factory_list[0]
#                  ).setServiceParent(serviceCollection)
#internet.TCPServer(10201, cs.factory_list[1]
#                   ).setServiceParent(serviceCollection)
