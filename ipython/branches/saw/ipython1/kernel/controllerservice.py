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
#                           Benjamin Ragan-Kelley <benjaminrk@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import os, sys

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
    
from ipython1.config import cutils

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
        
    def registerEngine(remoteEngine, id=None, ip=None, port=None, 
        pid=None):
        """Register new remote engine.
        
        remoteEngine: an implementer of IEngineCore, IEngineSerialized
            and IEngineQueued
        id: requested id
        
        Returns a dict of {'id':id} and possibly other key, value pairs..
        """
    
    def unregisterEngine(id):
        """Handle a disconnecting engine."""
        
    def onRegisterEngineDo(f, includeID, *args, **kwargs):
        """call f with *args and **kwargs when an engine is registered.  
        If includeID is True, the first argument will be the id"""
    
    def onUnregisterEngineDo(f, includeID, *args, **kwargs):
        """call f with *args and **kwargs when an engine is unregistered.  
        If includeID is True, the first argument will be the id"""
    
    def onRegisterEngineDoNot(f):
        """stop calling f on registration"""
    
    def onUnregisterEngineDo(f):
        """stop calling f on unregistration"""
                
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
        self._onRegister = []
        self._onUnregister = []
    
    #---------------------------------------------------------------------------
    # Methods used to save the engine info to a log file
    #---------------------------------------------------------------------------
    
    def _buildEngineInfoString(self, id, ip, port, pid):
        if id is None:
            id = -99
        if ip is None:
            ip = "-99"
        if port is None:
            port = -99
        if pid is None:
            pid = -99
        return "Engine Info: %d %s %d %d" % (id, ip , port, pid)
        
    def _logEngineInfo(self, id, ip, port, pid):
        log.msg(self._buildEngineInfoString(id,ip,port,pid))
    
    def _getEngineInfoLogFile(self):
        # Store all logs inside the ipython directory
        ipdir = cutils.getIpythonDir()
        pjoin = os.path.join
        logdir_base = pjoin(ipdir,'log')
        if not os.path.isdir(logdir_base):
            os.makedirs(logdir_base)
        logfile = os.path.join(logdir_base,'ipcontroller-%s-engine-info.log' % os.getpid())
        return logfile
    
    def _logEngineInfoToFile(self, id, ip, port, pid):
        """Log info about an engine to a log file.
        
        When an engine registers with a ControllerService, the ControllerService
        saves information about the engine to a log file.  That information
        can be useful for various purposes, such as killing hung engines, etc.
        
        This method takes the assigned id, ip/port and pid of the engine
        and saves it to a file of the form:
        
        ~/.ipython/log/ipcontroller-###-engine-info.log
        
        where ### is the pid of the controller.
        
        Each line of this file has the form:
        
        Engine Info: ip ip port pid
        
        If any of the entries are not known, they are replaced by -99.
        """
        
        fname = self._getEngineInfoLogFile()
        f = open(fname, 'a')
        s = self._buildEngineInfoString(id,ip,port,pid)
        f.write(s + '\n')
        f.close()
    
    #---------------------------------------------------------------------------
    # IControllerCore methods
    #---------------------------------------------------------------------------
        
    def registerEngine(self, remoteEngine, id=None,
        ip=None, port=None, pid=None):
        """Register new engine connection"""
        
        # What happens if these assertions fail?
        assert IEngineCore.providedBy(remoteEngine), \
            "engine passed to registerEngine doesn't provide IEngineCore"
        assert IEngineSerialized.providedBy(remoteEngine), \
            "engine passed to registerEngine doesn't provide IEngineSerialized"
        assert IEngineQueued.providedBy(remoteEngine), \
            "engine passed to registerEngine doesn't provide IEngineQueued"
        assert isinstance(id, int) or id is None, \
            "id  to registerEngine must be an integer or None"
        assert isinstance(ip, str) or ip is None, \
            "ip  to registerEngine must be a string or None"
        assert isinstance(port, int) or port is None, \
            "port to registerEngine must be an integer or None"
        assert isinstance(pid, int) or pid is None, \
            "pid to registerEngine must be an integer or None"
            
        desiredID = id
        if desiredID in self.engines.keys():
            desiredID = None
            
        if desiredID in self.availableIDs:
            getID = desiredID
            self.availableIDs.remove(desiredID)
        else:
            getID = self.availableIDs.pop()
        remoteEngine.id = getID
        remoteEngine.service = self
        self.engines[getID] = remoteEngine

        # Log the Engine Information for monitoring purposes
        self._logEngineInfoToFile(getID, ip, port, pid)

        msg = "registered engine: %i" %getID
        log.msg(msg)
        
        for i in range(len(self._onRegister)):
            (f,args,kwargs,ifid) = self._onRegister[i]
            try:
                if ifid:
                    f(getID, *args, **kwargs)
                else:
                    f(*args, **kwargs)
            except:
                self._onRegister.pop(i)
        
        return {'id':getID}
    
    def unregisterEngine(self, id):
        """Unregister remote engine object"""
        
        msg = "unregistered engine %i" %id
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
    
        for i in range(len(self._onUnregister)):
            (f,args,kwargs,ifid) = self._onUnregister[i]
            try:
                if ifid:
                    f(id, *args, **kwargs)
                else:
                    f(*args, **kwargs)
            except:
                self._onUnregister.pop(i)
    
    def onRegisterEngineDo(self, f, includeID, *args, **kwargs):
        assert callable(f), "f must be callable"
        self._onRegister.append((f,args,kwargs,includeID))

    def onUnregisterEngineDo(self, f, includeID, *args, **kwargs):
        assert callable(f), "f must be callable"
        self._onUnregister.append((f,args,kwargs,includeID))
    
    def onRegisterEngineDoNot(self, f):
        for i in range(len(self._onRegister)):
            g = self._onRegister[i][0]
            if f == g:
                self._onRegister.pop(i)
                return
    
    def onUnregisterEngineDoNot(self, f):
        for i in range(len(self._onUnregister)):
            g = self._onUnregister[i][0]
            if f == g:
                self._onUnregister.pop(i)
                return

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
        
    def registerEngine(self, remoteEngine, id=None,
        ip=None, port=None, pid=None):
        return self.controller.registerEngine(remoteEngine, 
            id, ip, port, pid)
    
    def unregisterEngine(self, id):
        return self.controller.unregisterEngine(id)


