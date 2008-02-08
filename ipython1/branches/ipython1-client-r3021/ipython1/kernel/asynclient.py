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

AsynRemoteController = AsynMultiEngineController

defaultAddress = (co['client']['connectToMultiEngineControllerOn']['ip'],
    co['client']['connectToMultiEngineControllerOn']['port'])
"""The (ip,port) tuple of the default MultiEngineController."""


