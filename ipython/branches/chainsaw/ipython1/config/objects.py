#!/usr/bin/env python
# encoding: utf-8
"""
Configuration objects.

I don't know how to deal with config objects that have the same attributes.  Solutions:

- Make sure each config object has uniquely named attributes.
- Have a separate config file for each config object.  This is what I do now.

"""

# Imports

from ipython1.kernel.enginevanilla import \
    IVanillaEngineClientFactory, IVanillaEngineServerFactory

from ipython1.kernel.controllervanilla import \
    IVanillaControllerFactory, RemoteController

from ipython1.core.shell import InteractiveShell

# A base class for configuration objects

class Configuration(object):
    
    configFiles = ['ipython1rc.py']
    
    def update(self, **kwargs):
        for k, v in kwargs.iteritems():
            if hasattr(self, k):
                print "Setting %s to: " % k + repr(v)
                setattr(self, k, v)
            else:
                pass
                #raise AttributeError("Configuration object does not have attribute: " + k)

    def addConfigFile(self, filename):
        self.configFiles.append(filename)

# Global defaults
    
maxMesageSize = 999999
enginePort = 10201
clientVanillaPort = 10105

# Engine configration

class EngineConfiguration(Configuration):
    connectToControllerOn = ('127.0.0.1', enginePort)
    engineClientProtocolInterface = IVanillaEngineClientFactory
    engineShell = InteractiveShell
    maxMessageSize = maxMesageSize
    mpiImportStatement = ''
    
# Controller configruation
    
class ControllerConfiguration(Configuration):
    engineServerProtocolInterface = IVanillaEngineServerFactory
    listenForEnginesOn  = ('', enginePort)
    clientInterfaces = [(IVanillaControllerFactory, ('', clientVanillaPort))]
    maxMessageSize = maxMesageSize
    
# Client configuration

class ClientConfiguration(Configuration):
    
    configFiles = ['client_config.py']
    
    RemoteController = RemoteController
    connectToControllerOn = ('127.0.0.1', clientVanillaPort)
    maxMessageSize = maxMesageSize




