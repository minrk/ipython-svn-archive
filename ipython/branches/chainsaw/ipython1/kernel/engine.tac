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
try:
	from ipython1.kernel.engineservice import EngineService
	from ipython1.kernel import enginepb
except ImportError:
    print "ipython1 needs to be in your PYTHONPATH"

#init service:

application = service.Application('engine', uid=1, gid=1)
serviceCollection = service.IServiceCollection(application)

pbfact = pb.PBClientFactory()
es = EngineService('localhost', 10106, pbfact)
es.setServiceParent(serviceCollection)

pEngine = enginepb.PerspectiveEngineFromService(es)
pbfact.getRootObject().addCallbacks(pEngine._success, pEngine._failure)