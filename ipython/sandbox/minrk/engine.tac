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
from twisted.spread import pb
from twisted.internet import reactor

from ipython1.kernel.engineservice import EngineService
from ipython1.kernel import enginepb

application = service.Application('engine', uid=1, gid=1)
serviceCollection = service.IServiceCollection(application)

es = EngineService()
pEngine = enginepb.PBEngineFromService(es)
pbfact = pb.PBClientFactory()

reactor.connectTCP('localhost', 10201, pbfact)
pEngine.connect(pbfact)

es.setServiceParent(serviceCollection)

