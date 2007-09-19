#!/usr/bin/env python
"""The ipython controller.
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

import sys, time, os
from optparse import OptionParser

from twisted.internet import reactor, error
from twisted.python import log

from ipython1.kernel import controllerservice
from ipython1.kernel.multiengine import IMultiEngine
from ipython1.kernel.task import ITaskController

from ipython1.kernel.config import configManager as kernelConfigManager

def main(logfile):
    co = kernelConfigManager.getConfigObj()
    if logfile:
        logfile = logfile + str(os.getpid()) + '.log'
        try:
            openLogFile = open(logfile, 'w')
        except:
            openLogFile = sys.stdout
    else:
        openLogFile = sys.stdout
    log.startLogging(openLogFile)
    
    # Execute any user defined import statements
    cis = co['controller']['controllerImportStatement']
    if cis:
        try:
            exec cis
        except:
            log.msg("Error running controllerImportStatement: %s" % cis)
    
    # Create and configure the core ControllerService
    cs = controllerservice.ControllerService()
    
    # Start listening for engines
    efac = kernelConfigManager.asImportable(co['controller']['engineServerProtocolInterface'])(cs)
    reactor.listenTCP(
        port=co['controller']['listenForEnginesOn'].as_int('port'),
        factory=efac,
        interface=co['controller']['listenForEnginesOn']['ip'])
        
    for ciname, ci in co['controller']['controllerInterfaces'].iteritems():
        log.msg("Starting controller interface: " + ciname)
        adaptedController = kernelConfigManager.asImportable(ci['controllerInterface'])(cs)
        for niname, ni in ci['networkInterfaces'].iteritems():
            log.msg("Starting controller network interface (%s): %s:%s:%i" % (ciname,niname,ni['ip'],ni.as_int('port')))
            fac = kernelConfigManager.asImportable(ni['interface'])(adaptedController)
            reactor.listenTCP(
                port=ni.as_int('port'),
                factory=fac,
                interface=ni['ip'])
                    
    # Start the controller service and set things running
    cs.startService()
    reactor.run()

def start():
    parser = OptionParser()
    parser.set_defaults(logfile='')
        
    parser.add_option("--engine-port", type="int", dest="engineport",
        help="the TCP port the controller will listen on for engine connections")
    parser.add_option("--engine-ip", type="string", dest="engineip",
        help="the TCP ip address the controller will listen on for engine connections")
        
    parser.add_option("--task-port", type="int", dest="taskport",
        help="the TCP port the controller will listen on for task client connections")
    parser.add_option("--task-ip", type="string", dest="taskip",
        help="the TCP ip address the controller will listen on for task client connections")

    parser.add_option("--remote-cont-port", type="int", dest="rcport",
        help="the TCP port the controller will listen on for Remote Controller client connections")
    parser.add_option("--remote-cont-ip", type="string", dest="rcip",
        help="the TCP ip address the controller will listen on for Remote Controller client connections")

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
    #     config.updateConfigWithProfile('ipcontroller', options.profile, options.ipythondir)
    # elif options.rcfile and not options.profile:
    #     config.updateConfigWithFile(options.rcfile, options.ipythondir)
    # else:
    kernelConfigManager.updateConfigObjFromDefaultFile(options.ipythondir)
    co = kernelConfigManager.getConfigObj()
    
    # Update with command line options
    if options.engineip is not None:
        co['controller']['listenForEnginesOn']['ip'] = options.engineip
    if options.engineport is not None:
        co['controller']['listenForEnginesOn']['port'] = options.engineport
    di = co['controller']['controllerInterfaces']['multiengine']['default']
    if options.rcip is not None:
        co['controller']['controllerInterfaces']['multiengine']['networkInterfaces'][di]['ip'] = options.rcip
    if options.rcport is not None:
        co['controller']['controllerInterfaces']['multiengine']['networkInterfaces'][di]['port'] = options.rcport
    di = co['controller']['controllerInterfaces']['task']['default']
    if options.taskip is not None:
        co['controller']['controllerInterfaces']['task']['networkInterfaces'][di]['ip'] = options.taskip
    if options.taskport is not None:
        co['controller']['controllerInterfaces']['task']['networkInterfaces'][di]['port'] = options.taskport

    kernelConfigManager.updateConfigObj(co)
    print kernelConfigManager.getConfigObj()
    main(options.logfile)
    
    
if __name__ == "__main__":
    start()
