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

RemoteController = MultiEngineController

defaultMECAddress = (co['client']['connectToMultiEngineControllerOn']['ip'],
    co['client']['connectToMultiEngineControllerOn']['port'])
"""The (ip,port) tuple of the default MultiEngineController."""

from ipython1.kernel.task import Task, Dependency

TaskController = kernelConfigManager._import(co['client']['TaskController'])
"""The default TaskController class obtained from config information."""

defaultTCAddress = (co['client']['connectToTaskControllerOn']['ip'],
    co['client']['connectToTaskControllerOn']['port'])
"""The (ip,port) tuple of the default task controller."""


rit = ReactorInThread()
rit.setDaemon(True)
rit.start()