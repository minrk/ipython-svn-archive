#!/usr/bin/env python
# encoding: utf-8


from ipython1.kernel import codeutil
import ipython1.kernel.magic
from ipython1.kernel.multiengineclient import IFullBlockingMultiEngineClient
from ipython1.kernel.taskclient import IBlockingTaskClient
from ipython1.kernel.task import Task, Dependency
from ipython1.kernel.twistedutil import ReactorInThread
from ipython1.kernel.config import configManager as kernelConfigManager

co = kernelConfigManager.get_config_obj()

SynchronousMultiEngine = kernelConfigManager._import(co['client']['MultiEngineImplementation'])
"""The default MultiEngineController class obtained from config information."""

def MultiEngineController(addr):
    """The default MultiEngineController class."""
    smultiengine = SynchronousMultiEngine(addr)
    return IFullBlockingMultiEngineClient(smultiengine)

def RemoteController(addr):
    print "The RemoteController class is deprecated, please use MultiEngineController instead"
    return MultiEngineController(addr)

default_address = (co['client']['connectToMultiEngineControllerOn']['ip'],
    co['client']['connectToMultiEngineControllerOn']['port'])
"""The (ip,port) tuple of the default MultiEngineController."""

default_remote_controller = default_address



def TaskController(addr):
    """The default TaskController class obtained from config information."""
    _task_controller = kernelConfigManager._import(co['client']['TaskControllerImplementation'])
    return IBlockingTaskClient(_task_controller(addr))

default_task_address = (co['client']['connectToTaskControllerOn']['ip'],
    co['client']['connectToTaskControllerOn']['port'])
"""The (ip,port) tuple of the default task controller."""

default_task_controller = default_task_address



rit = ReactorInThread()
rit.setDaemon(True)
rit.start()