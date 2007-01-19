# encoding: utf-8
# -*- test-case-name: ipython1.test.test_controllerservice -*-
"""A Twisted Service for the IPython Controller.

The IPython Controller:

 * Listens for Engines to connect and then manages those Engines.
 * Listens for clients and passes commands from client to the Engines.
 * Exposes an asynchronous interfaces to the Engines which themselves can block.
 * Acts as a gateway to the Engines.

The design of the controller is somewhat abstract to allow flexibility in how 
the controller is presented to clients.  This idea is that there is a basic
ControllerService class that allows engines to connect to it.  But, this 
basic class has no client interfaces.  To develop client interfaces developer
provides an adapter that makes the ControllerService look like something.  For 
example, one client interface might support task farming and another might
support interactive usage.  The important thing is that by using interfaces
and adapters, a single controller can be accessed from multiple interfaces.
Furthermore, by adapting various client interfaces to various network
protocols, each client interface can be exposed to multiple network protocols.
See multiengine.py for an example of how to adapt the ControllerService
to a client interface.
"""
__docformat__ = "restructuredtext en"
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

from twisted.application import service
from twisted.internet import defer, reactor
from twisted.python import log, components
from zope.interface import Interface, implements, Attribute
import zope.interface as zi

from ipython1.kernel.serialized import Serialized
from ipython1.kernel.engineservice import \
    IEngineCore, \
    IEngineSerialized, \
    IEngineQueued


#-------------------------------------------------------------------------------
# Interfaces for the Controller
#-------------------------------------------------------------------------------

class IControllerCore(Interface):
    """Basic methods any controller must have.
    
    This is basically the aspect of the controller relevant to the 
    engines and does not assume anything about how the engines will
    be presented to a client.
    """
        
    engines = Attribute("A dict of engine ids and engine instances.")
        
    def registerEngine(remoteEngine, id):
        """Register new remote engine.
        
        remoteEngine: an implementer of IEngineCore, IEngineSerialized
            and IEngineQueued
        id: requested id
        
        Returns a dict of {'id':id} and possibly other key, value pairs..
        """
    
    def unregisterEngine(id):
        """Handle a disconnecting engine."""
        
                
class IControllerBase(IControllerCore):
    """The basic controller interface."""
    pass 


#-------------------------------------------------------------------------------
# Implementation of the ControllerService
#-------------------------------------------------------------------------------

class ControllerService(object, service.Service):
    """A basic Controller represented as a Twisted Service.
    
    This class doesn't implement any client notification mechanism.  That
    is up to adapted subclasses.
    """
    
    # I also pick up the IService interface by inheritance from service.Service
    implements(IControllerBase)
    
    def __init__(self, maxEngines=255, saveIDs=False):
        self.saveIDs = saveIDs
        self.engines = {}
        self.availableIDs = range(maxEngines,-1,-1)   # [255,...,0]
    
    #---------------------------------------------------------------------------
    # IControllerCore methods
    #---------------------------------------------------------------------------
        
    def registerEngine(self, remoteEngine, id=None):
        """Register new engine connection"""
        
        # What happens if these assertions fail?
        assert IEngineCore.providedBy(remoteEngine), \
            "engine passed to registerEngine doesn't provide IEngineCore"
        assert IEngineSerialized.providedBy(remoteEngine), \
            "engine passed to registerEngine doesn't provide IEngineSerialized"
        assert IEngineQueued.providedBy(remoteEngine), \
            "engine passed to registerEngine doesn't provide IEngineQueued"
        
        desiredID = id
        if desiredID in self.engines.keys():
            desiredID = None
            
        if desiredID in self.availableIDs:
            remoteEngine.id = desiredID
            self.availableIDs.remove(desiredID)
        else:
            remoteEngine.id = self.availableIDs.pop()
            
        remoteEngine.service = self
        self.engines[remoteEngine.id] = remoteEngine
        msg = "registered engine: " + repr(remoteEngine.id)
        log.msg(msg)
        return {'id':remoteEngine.id}
    
    def unregisterEngine(self, id):
        """Unregister remote engine object"""
        
        msg = "unregistered engine %r" %id
        log.msg(msg)
        try:
            del self.engines[id]
        except KeyError:
            log.msg("engine %i was not registered" % id)
        else:
            if not self.saveIDs:
                self.availableIDs.append(id)
                # Sort to assign lower ids first
                self.availableIDs.sort(reverse=True) 
            else:
                log.msg("preserving id %i" %id)
    

#-------------------------------------------------------------------------------
# Base class for adapting controller to different client APIs
#-------------------------------------------------------------------------------

class ControllerAdapterBase(object):
    """All Controller adapters should inherit from this.
    
    This class provides a wrapped version of the IControllerBase interface that
    can be used to easily create new custom controllers.  Subclasses of this
    will provide a full implementation of IControllerBase.
    
    This class doesn't implement any client notification mechanism.  That
    is up to subclasses.
    """
    
    implements(IControllerBase)
    
    def __init__(self, controller):
        self.controller = controller
        # Needed for IControllerCore
        self.engines = self.controller.engines
        
    def registerEngine(self, remoteEngine, id=None):
        return self.controller.registerEngine(remoteEngine, id)
    
    def unregisterEngine(self, id):
        return self.controller.unregisterEngine(id)


