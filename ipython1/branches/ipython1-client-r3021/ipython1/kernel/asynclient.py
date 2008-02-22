#!/usr/bin/env python
# encoding: utf-8


from ipython1.kernel import codeutil
from ipython1.kernel.config import configManager as kernelConfigManager
from ipython1.kernel import multiengine as me
from ipython1.kernel.error import CompositeError

co = kernelConfigManager.get_config_obj()

SynchronousMultiEngine = kernelConfigManager._import(co['client']['MultiEngineImplementation'])
"""The default MultiEngineClient class obtained from config information."""

def AsynMultiEngineClient(addr):
    """The default Asynch. MultiEngineClient class."""
    smultiengine = SynchronousMultiEngine(addr)
    return me.IFullSynchronousTwoPhaseMultiEngine(smultiengine)

default_address = (co['client']['connectToMultiEngineControllerOn']['ip'],
    co['client']['connectToMultiEngineControllerOn']['port'])
"""The (ip,port) tuple of the default MultiEngineClient."""

def AsynTaskClient(addr):
    """The default TaskClient class obtained from config information."""
    _task_controller = kernelConfigManager._import(co['client']['TaskControllerImplementation'])
    return _task_controller(addr)

default_task_address = (co['client']['connectToTaskControllerOn']['ip'],
    co['client']['connectToTaskControllerOn']['port'])
"""The (ip,port) tuple of the default task controller."""

