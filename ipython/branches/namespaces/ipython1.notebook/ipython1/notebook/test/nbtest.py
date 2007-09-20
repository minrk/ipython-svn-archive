# encoding: utf-8
"""Utilities for making tests from Notebooks
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
# from twisted.python import log
from sys import stdout

from twisted.internet import defer

from ipython1.notebook import notebook, models, dbutil
from ipython1.kernel import engineservice as es
# from ipython1.test import DeferredTestCase

class NotebookTest(object):
    """A test From a notebook file"""
    
    def __init__(self, nbfile, logfile=None):
        if logfile:
            self.log = open(logfile, 'a')
        else:
            self.log = stdout
        
        dbutil.initDB()
        self.nbc = notebook.NotebookController(es.IEngineQueued(es.EngineService()))
        self.nbu = notebook.NotebookUser(self.nbc, 'test', 'test@localhost')
        self.user = self.nbu.user
        f = open(nbfile)
        nbs = f.read()
        f.close()
        if nbfile[-3:] == 'xml':
            self.nb = self.nbu.loadNotebookFromXML(nbs)
        else:
            self.nb = self.nbu.loadNotebookFromSparse(nbs)
    
    def _checkFailures(self, _):
        ntests = len(self.nbu.getNode(nodeType='inputCell'))
        for node, output in self.failures:
            self.log.write("Failed Input:\n%s\n"%node.input)
            if node.comment:
                self.log.write("Comments:\n%s\n"%node.comment)
            self.log.write("Expected Result:\n%s\n"%node.output)
            self.log.write("Received Result:\n%s\n"%output)
        self.log.write("Ran %i Tests, with %i Successes\n"%\
                        (ntests, ntests-len(self.failures)))
    
    def run(self):
        self.failures = []
        d = self.testNode(self.nb.root)
        d.addCallback(self._checkFailures)
        return d
    
    def _checkResult(self, result, node):
        success, output = result
        if success:
            self.log.write("[ OK ]\n")
        else:
            self.log.write("[FAIL]\n")
            self.failures.append((node, output))
    
    def testNode(self, node):
        if isinstance(node, models.Section):
            self.log.write("Test Section: %s\n"%node.title)
            self.log.write(node.comment+'\n')
            l = [self.testNode(n) for n in node.children]
            return defer.DeferredList(l)
        elif isinstance(node, models.InputCell):
            self.log.write("Test..........................")
            d = self.nbu.execute(node.nodeID, test=True).addCallback(self._checkResult, node)
            return d
        elif isinstance(node, models.TextCell):
            self.log.write(node.textData+'\n')
            return defer.succeed(None)
        
    
