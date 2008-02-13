#!/usr/bin/env python
# encoding: utf-8


from ipython1.kernel import codeutil
from ipython1.kernel.config import configManager as kernelConfigManager
from ipython1.kernel import multiengine as me

co = kernelConfigManager.getConfigObj()

SynchronousMultiEngine = kernelConfigManager._import(co['client']['MultiEngineImplementation'])
"""The default MultiEngineController class obtained from config information."""

def AsynMultiEngineController(addr):
    """The default Asynch. MultiEngineController class."""
    smultiengine = SynchronousMultiEngine(addr)
    return me.IFullSynchronousTwoPhaseMultiEngine(smultiengine)

defaultAddress = (co['client']['connectToMultiEngineControllerOn']['ip'],
    co['client']['connectToMultiEngineControllerOn']['port'])
"""The (ip,port) tuple of the default MultiEngineController."""

def AsynTaskController(addr):
    """The default TaskController class obtained from config information."""
    _task_controller = kernelConfigManager._import(co['client']['TaskControllerImplementation'])
    return _task_controller(addr)

defaultTaskAddress = (co['client']['connectToTaskControllerOn']['ip'],
    co['client']['connectToTaskControllerOn']['port'])
"""The (ip,port) tuple of the default task controller."""

defaultTaskController = defaultTaskAddress
