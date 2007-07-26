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

# import os.path
from twisted.trial import unittest
from sqlalchemy.exceptions import InvalidRequestError

from ipython1.notebook import notebook, dbutil, xmlutil
from ipython1.kernel.error import NotFoundError
from ipython1.notebook.models import TextCell, InputCell, Section

# get warning out of the way of test output
engine = dbutil.sqla.create_engine("sqlite:///")
class NotebookTestCase(unittest.TestCase):
            
    def setUp(self):
        dbutil.initDB("sqlite:///")
        self.nbc = notebook.NotebookController()
        self.u = notebook.NotebookUser(self.nbc, 'userA', 'userA@email')
        self.nb = self.u.addRootSection('title')
    
    def testappendNode(self):
        clist = [TextCell(),InputCell(),Section(),TextCell(),InputCell()]
        for c in clist:
            self.u.addNode(self.nb.nodeID, c)
        self.assertEquals(clist, self.nb.children)
    
    def testprependNode(self):
        clist = [TextCell(),InputCell(),Section(),TextCell(),InputCell()]
        nb = self.u.addRootSection('title')
        for c in clist:
            self.u.addNode(self.nb.nodeID, c, 0)
        clist.reverse()
        self.assertEquals(clist, self.nb.children)
    
    def testinsertNode(self):
        clist = [TextCell(),InputCell(),Section(),TextCell(),InputCell()]
        nb = self.u.addRootSection('title')
        for c in clist:
            self.u.addNode(self.nb.nodeID, c, 1)
        clist = clist[:1]+clist[-1:-5:-1]
        self.assertEquals(clist, self.nb.children)
    
    def testdropNode(self):
        c = TextCell()
        self.u.addNode(self.nb.nodeID, c)
        self.assertEquals(self.u.user.nodes,[self.nb, c])
        self.u.dropNode(c.nodeID)
        self.assertEquals(self.u.user.nodes,[self.nb])
        self.assertEquals(self.nb.children,[])
    
    def testeditNode(self):
        c = TextCell()
        self.u.addNode(self.nb.nodeID, c)
        mod1 = c.dateModified
        self.u.editNode(c.nodeID, comment="some comment")
        self.assertEquals(c.comment,"some comment")
        self.assertNotEquals(c.dateModified,mod1)
    
    def testmultiUser(self):
        self.assertRaises(AssertionError, notebook.NotebookUser, self.nbc, 'userA')
        self.assertRaises(AssertionError, notebook.NotebookUser, self.nbc, 'userB')
        del self.u
        self.assertEquals(self.nbc.users, [])
        ua = notebook.NotebookUser(self.nbc, 'userA')
        ub = notebook.NotebookUser(self.nbc, 'userB', 'b@email')
        self.assertEquals(self.nbc.users, [ua.user.userID, ub.user.userID])
        c = TextCell()
        self.assertRaises(NotFoundError, ub.addNode, self.nb.nodeID, c)
        self.assertRaises(NotFoundError, ub.addNode, 73, c)
        nb = ub.addRootSection('title')
        ub.addNode(nb.nodeID, c)
        c2 = InputCell()
        self.assertRaises(AssertionError, ub.addNode, c.nodeID, c2)
    
        
        
        
    



