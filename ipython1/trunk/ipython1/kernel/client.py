#!/usr/bin/env python
# encoding: utf-8

import sys

from ipython1.tools import growl
growl.start("IPython1 Client")

from ipython1.kernel import codeutil
import ipython1.kernel.magic
from ipython1.kernel.multiengineclient import IFullBlockingMultiEngineClient
from ipython1.kernel.taskclient import IBlockingTaskClient
from ipython1.kernel.task import Task
from ipython1.kernel.twistedutil import ReactorInThread
from ipython1.kernel.config import configManager as kernelConfigManager
from ipython1.kernel.error import CompositeError

co = kernelConfigManager.get_config_obj()

SynchronousMultiEngine = kernelConfigManager._import(co['client']['MultiEngineImplementation'])
"""The default MultiEngineClient class obtained from config information."""

def MultiEngineClient(addr):
    """The default MultiEngineClient class."""
    smultiengine = SynchronousMultiEngine(addr)
    return IFullBlockingMultiEngineClient(smultiengine)

def RemoteController(addr):
    print "The RemoteController class is deprecated, please use MultiEngineClient instead"
    return MultiEngineClient(addr)

default_address = (co['client']['connectToMultiEngineControllerOn']['ip'],
    co['client']['connectToMultiEngineControllerOn']['port'])
"""The (ip,port) tuple of the default MultiEngineClient."""


def TaskClient(addr):
    """The default TaskClient class obtained from config information."""
    _task_controller = kernelConfigManager._import(co['client']['TaskControllerImplementation'])
    return IBlockingTaskClient(_task_controller(addr))

default_task_address = (co['client']['connectToTaskControllerOn']['ip'],
    co['client']['connectToTaskControllerOn']['port'])
"""The (ip,port) tuple of the default task controller."""


rit = ReactorInThread()
rit.setDaemon(True)
rit.start()