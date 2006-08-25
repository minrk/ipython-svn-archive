#!/usr/bin/env python
# encoding: utf-8
"""
Configuration objects
"""

# Imports

from ipython1.kernel.enginevanilla import \
    IVanillaEngineClientFactory, IVanillaEngineServerFactory

from ipython1.kernel.controllervanilla import \
    IVanillaControllerFactory

from ipython1.kernel import \
    controllerclient

# A base class for configuration objects

class Configuration(object):
    
    def update(self, **kwargs):
        for k, v in kwargs.iteritems():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise AttributeError("Configration object does not have attribute: " + k)

# Global defautls
    
maxMesageSize = 999999
enginePort = 10201

# Engine configration

class EngineConfiguration(Configuration):
    enginePort = enginePort
    engineClientProtocolInterface = IVanillaEngineClientFactory
    maxMessageSize = maxMesageSize
    mpiImportStatement = ''
    
# Controller configruation
    
class ControllerConfiguration(Configuration):
    enginePort = enginePort
    engineServerProtocolInterface = IVanillaEngineServerFactory
    clientInterfaces = [(IVanillaControllerFactory, 10105)]
    maxMessageSize = maxMesageSize
    
# Client configuration

class ClientConfiguration(Configuration):
    clientModule = controllerclient
    controllerPort = 10105
    maxMessageSize = maxMesageSize




