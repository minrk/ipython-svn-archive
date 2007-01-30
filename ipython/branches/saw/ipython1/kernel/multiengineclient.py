# encoding: utf-8
# -*- test-case-name: ipython1.test.test_multiengineclient -*-
"""General Classes for IMultiEngine clients.
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

import cPickle as pickle

from twisted.internet import reactor
from twisted.python import components
from twisted.python.failure import Failure
from twisted.spread import pb
from zope.interface import Interface, implements

import ipython1.kernel.pbconfig
from ipython1.kernel.multiengine import MultiEngine, IMultiEngine
from ipython1.kernel.blockon import blockOn
from ipython1.kernel.util import gatherBoth



#-------------------------------------------------------------------------------
# The PB version of RemoteController
#-------------------------------------------------------------------------------

class ConnectingMultiEngineClient(object):
    """A synchronous high-level PBRemoteController."""
    
    def __init__(self, addr):
        self.addr = addr
        self.multiengine = None
        self.block = False
        self.connected = False
                
    def _blockOrNot(self, d):
        if self.block:
            return blockOn(d)
        else:
            return d
           
    def blockOn(self, d):
        return blockOn(d)
            
    #---------------------------------------------------------------------------
    # Methods for subclasses to override
    #---------------------------------------------------------------------------
            
    def connect(self):
        """Create self.multiengine and set self.connected to True."""
        pass
            
    #---------------------------------------------------------------------------
    # Interface methods
    #---------------------------------------------------------------------------

    def execute(self, targets, lines):
        self.connect()
        d = self.multiengine.execute(targets, lines)
        return self._blockOrNot(d)
        
    def executeAll(self, lines):
        return self.execute('all', lines)
        
    def push(self, targets, **namespace):
        self.connect()
        d = self.multiengine.push(targets, **namespace)
        return self._blockOrNot(d)
        
    def pushAll(self, **namespace):
        return self.push('all', **namespace)
        
    def pull(self, targets, *keys):
        self.connect()
        d = self.multiengine.pull(targets, *keys)
        return self._blockOrNot(d)
    
    def pullAll(self, *keys):
        return self.pull('all', *keys)
    
    def getResult(self, targets, i=None):
        self.connect()
        d = self.multiengine.getResult(targets, i)
        return self._blockOrNot(d)     
    
    def getResultAll(self, i=None):
        return self.getResult('all', i)
    
    def reset(self, targets):
        self.connect()
        d = self.multiengine.reset(targets)
        return self._blockOrNot(d)
    
    def resetAll(self):
        return self.reset('all')
    
    def keys(self, targets):
        self.connect()
        d = self.multiengine.keys(targets)
        return self._blockOrNot(d)
    
    def keysAll(self):
        return self.keys('all')
    
    def kill(self, targets, controller=False):
        self.connect()
        d = self.multiengine.kill(targets, controller)
        return self._blockOrNot(d)
        
    def killAll(self, controller=False):
        return self.kill('all', controller)
    
    def pushSerialized(self, targets, **namespace):
        self.connect()
        d = self.multiengine.pushSerialized(targets, **namespace)
        return self._blockOrNot(d)
    
    def pushSerializedAll(self, **namespace):
        return self.pushSerialized('all', **namespace)
    
    def pullSerialized(self, targets, *keys):
        self.connect()
        d = self.multiengine.pullSerialized(targets, *keys)
        return self._blockOrNot(d)
    
    def pullSerializedAll(self, *keys):
        return self.pullSerialized('all', *keys)
    
    def clearQueue(self, targets):
        self.connect()
        d = self.multiengine.clearQueue(targets)
        return self._blockOrNot(d)
    
    def clearQueueAll(self):
        return self.clearQueue('all')
    
    def queueStatus(self, targets):
        self.connect()
        d = self.multiengine.queueStatus(targets)
        return self._blockOrNot(d)
    
    def queueStatusAll(self):
        return self.queueStatus('all')
        
    def getIDs(self):
        self.connect()
        d = self.multiengine.getIDs()
        return self._blockOrNot(d)
    
    def verifyTargets(self, targets):
        self.connect()
        d = self.multiengine.verifyTargets(targets)
        return self._blockOrNot(d)
        
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        self.connect()
        d = self.multiengine.scatter(targets, key, seq, style, flatten)
        return self._blockOrNot(d)
    
    def gather(self, targets, key, style='basic'):
        self.connect()
        d = self.multiengine.gather(targets, key, style)
        return self._blockOrNot(d)