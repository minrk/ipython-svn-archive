#!/usr/bin/env python
"""Start the IPython Engine.
"""

#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelley <benjaminrk@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

# Python looks for an empty string at the beginning of sys.path to enable
# importing from the cwd.
import sys
sys.path.insert(0, '')

import sys, os
from optparse import OptionParser

from twisted.internet import reactor
from twisted.python import log

from ipython1.kernel.engineservice import EngineService

from ipython1.kernel.config import configManager as kernelConfigManager
from ipython1.core.config import configManager as coreConfigManager

# MPI module should be loaded first
# BEG 9/20/07: I don't think we need to do this first anymore.  Let's leave this here for a while
# and make sure of this.
# mpi = None
# kco = kernelConfigManager.getConfigObj()
# mpiis = kco['mpi']['mpiImportStatement']
# if mpiis:
#     try:
#         exec mpiis
#     except ImportError:
#         mpi = None

def main(n, logfile):
    kco = kernelConfigManager.getConfigObj()
    cco = coreConfigManager.getConfigObj()
    
    mpikey = kco['mpi']['default']
    mpiImportStatement = kco['mpi'].get(mpikey, None)
    if mpiImportStatement is not None:
        try:
            exec mpiImportStatement
        except:
            mpi = None
    else:
        mpi = None

    if logfile:
        logfile = logfile + str(os.getpid()) + '.log'
        try:
            openLogFile = open(logfile, 'w')
        except:
            openLogFile = sys.stdout
    else:
        openLogFile = sys.stdout
    log.startLogging(openLogFile)
    
    for i in range(n):
        shellClass = coreConfigManager._import(cco['shell']['shellClass'])
        service = EngineService(shellClass, mpi=mpi)
        fac = kernelConfigManager._import(kco['engine']['engineClientProtocolInterface'])(service)
        reactor.connectTCP(
            host=kco['engine']['connectToControllerOn']['ip'], 
            port=kco['engine']['connectToControllerOn'].as_int('port'),
            factory=fac)
        service.startService()
        sis = cco['shell']['shellImportStatement']
        if sis:
            try:
                service.execute(sis)
            except:
                log.msg("Error running shellImportStatement: %s" % sis)
                
    reactor.run()

def start(n=1):
    parser = OptionParser()
    parser.set_defaults(n=n)
    parser.set_defaults(profile = '')
    parser.set_defaults(rcfile='')
    parser.set_defaults(ipythondir='')
    parser.set_defaults(logfile='')

    parser.add_option("--controller-port", type="int", dest="controllerport",
        help="the TCP port the controller is listening on")
    parser.add_option("--controller-ip", type="string", dest="controllerip",
        help="the TCP ip address of the controller")
    parser.add_option("--mpi", type="string", dest="mpi",
        help="How to enable MPI (mpi4py, pytrilinos, or empty string to disable)")
    parser.add_option("-n", "--num", type="int", dest="n",
        help="the number of engines to start in this process")
    parser.add_option("-l", "--logfile", type="string", dest="logfile",
        help="log file name (default is stdout)")
    
    # Configuration files and profiles
    # parser.add_option("-p", "--profile", type="string", dest="profile",
    #     help="the name of a profile")
    # parser.add_option("--rcfile", type="string", dest="rcfile",
    #     help="the name of a configuration file")
    parser.add_option("--ipythondir", type="string", dest="ipythondir",
        help="look for config files and profiles in this directory")
    (options, args) = parser.parse_args()
            
    # Configuration files and profiles
    # if options.profile and not options.rcfile:
    #     config.updateConfigWithProfile('ipengine', options.profile, options.ipythondir)
    # elif options.rcfile and not options.profile:
    #     config.updateConfigWithFile(options.rcfile, options.ipythondir)
    # else:
    kernelConfigManager.updateConfigObjFromDefaultFile(options.ipythondir)
    coreConfigManager.updateConfigObjFromDefaultFile(options.ipythondir)

    kco = kernelConfigManager.getConfigObj()
    # Now override with command line options
    if options.controllerip is not None:
        kco['engine']['connectToControllerOn']['ip'] = options.controllerip
    if options.controllerport is not None:
        kco['engine']['connectToControllerOn']['port'] = options.controllerport
    if options.mpi is not None:
        kco['mpi']['default'] = options.mpi
            
    main(options.n, options.logfile)
    
if __name__ == "__main__":
    start()
