# encoding: utf-8
"""
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

# from twisted.internet import defer
from twisted.trial import unittest
from ipython1.notebook import notebook, dbutil, xmlutil
from ipython1.notebook.models import TextCell, InputCell, Section
    
class NotebookTestCase(unittest.TestCase):
            
    def setUp(self):
        dbutil.initDB("sqlite:///")
        self.nc = notebook.NotebookController()
        self.users = [notebook.NotebookUser(self.nc, 'userA', 'userA@email')]
        
        
    def tearDown(self):
        for u in self.users:
            u.disconnect()
            
    def testappendNode(self):
        u = self.users[0]
        clist = [TextCell(),InputCell(),Section(),TextCell(),InputCell()]
        nb = u.addRootSection('title')
        for c in clist:
            u.addNode(nb.nodeID, c)
        self.assertEquals(clist, nb.children)
    
    def testprependNode(self):
        u = self.users[0]
        clist = [TextCell(),InputCell(),Section(),TextCell(),InputCell()]
        nb = u.addRootSection('title')
        for c in clist:
            u.addNode(nb.nodeID, c, 0)
        clist.reverse()
        self.assertEquals(clist, nb.children)
    



