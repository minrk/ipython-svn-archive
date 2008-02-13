#!/usr/bin/env python
# encoding: utf-8


from ipython1.kernel import codeutil
import ipython1.kernel.magic
from ipython1.kernel.multiengineclient import IFullBlockingMultiEngineClient
from ipython1.kernel.twistedutil import ReactorInThread
from ipython1.kernel.config import configManager as kernelConfigManager

co = kernelConfigManager.getConfigObj()

SynchronousMultiEngine = kernelConfigManager._import(co['client']['MultiEngineImplementation'])
"""The default MultiEngineController class obtained from config information."""

def MultiEngineController(addr):
    """The default MultiEngineController class."""
    smultiengine = SynchronousMultiEngine(addr)
    return IFullBlockingMultiEngineClient(smultiengine)

def RemoteController(addr):
    print "The RemoteController class is deprecated, please use MultiEngineController instead"
    return MultiEngineController(addr)

defaultAddress = (co['client']['connectToMultiEngineControllerOn']['ip'],
    co['client']['connectToMultiEngineControllerOn']['port'])
"""The (ip,port) tuple of the default MultiEngineController."""

defaultRemoteController = defaultAddress

from ipython1.kernel.task import Task, Dependency

TaskController = kernelConfigManager._import(co['client']['TaskController'])
"""The default TaskController class obtained from config information."""

defaultTaskAddress = (co['client']['connectToTaskControllerOn']['ip'],
    co['client']['connectToTaskControllerOn']['port'])
"""The (ip,port) tuple of the default task controller."""

defaultTaskController = defaultTaskAddress

rit = ReactorInThread()
rit.setDaemon(True)
rit.start()