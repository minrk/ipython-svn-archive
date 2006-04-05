#!/usr/bin/env python

from twisted.internet import reactor
from twisted.spread import pb

import ipython1.kernel.service as ipservice
 
ipcore = ipservice.IPythonCoreService()
reactor.listenTCP(10105, pb.PBServerFactory(IPerspectiveIPythonCore(ipcore))
reactor.run()