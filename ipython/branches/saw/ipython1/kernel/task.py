# encoding: utf-8
# -*- test-case-name: ipython1.test.test_task -*-
"""Task farming representation of the controller.
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

import zope.interface as zi

class IWorker(zi.Interface):
    
    def run(expression, namespace=None):
        """Run expression in namespace."""
        
        
class WorkerFromQueuedEngine(object):
    
    zi.implements(IWorker)
    
    def __init__(self, queuedEngine):
        self.queuedEngine = qe
        
    def run(expression, namespace=None):
        d1 = self.queuedEngine.push(**namespace)
        d1.addCallback(self.queuedEngine.execute('result = %s' % expression))
        d1.addCallback(self.queuedEngine.pull('result'))
        return d1
        
        
registerAdapter(WorkerFromQueuedEngine, IQueuedEngine, IWorker)

class ITaskController(zi.Interface):
    
    def run(expression, namespace=None):
        """Run a task"""
        
class TaskController(object):
    
    def __init__(self, controller):
        self.controller = controller
        
    def ruyn