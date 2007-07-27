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


from random import randint
from twisted.trial import unittest

from ipython1.notebook import notebook, dbutil, xmlutil
from ipython1.kernel.error import NotFoundError
from ipython1.notebook.models import TextCell, InputCell, Section, Node

# get warning out of the way of test output
engine = dbutil.sqla.create_engine("sqlite:///")
class NotebookTestCase(unittest.TestCase):
            
    def setUp(self):
        dbutil.initDB("sqlite:///")
        self.nbc = notebook.NotebookController()
        self.u = notebook.NotebookUser(self.nbc, 'userA', 'userA@email')
        self.nb = self.u.addRootSection('title')
    
    def loadNodes(self, n):
        l = []
        for _ in range(n):
            sections = self.nbc.nodeQuery.select_by(userID=self.u.user.userID, nodeType='section')
            # print sections
            parent = (sections + [None])[randint(0, len(sections))]
            if parent is None:
                l.append(self.u.addRootSection("title"))
            else:
                i = randint(1,3)
                if i == 1:
                    c = TextCell()
                elif i == 2:
                    c = InputCell()
                else:
                    c = Section()
                index = None
                if parent.children:
                    index = randint(0,len(parent.children)-1)
                l.append(self.u.addNode(parent.nodeID, c, index))
        return l
    
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
        self.assertNotEquals(c.dateModified, mod1)
    
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
    
    def testmergeUser(self):
        pass
    
    def testmoveNode(self):
        pass
    
    def testXML(self):
        session = self.nbc.session
        self.loadNodes(16)
        s = xmlutil.dumpDBtoXML(self.nbc.session, '/Users/minrk/s1.xml')
        u = self.u
        nodes = session.query(Node).select()
        kidl = map(getattr, u.user.notebooks, ['children']*len(u.user.notebooks))
        kidl = map(len, kidl)
        kidl.sort()
        before = [
        len(session.query(Section).select()),
        len(session.query(InputCell).select()),
        len(session.query(TextCell).select()),
        len([n for n in nodes if n.parentID]),
        len([n for n in nodes if n.parent]),
        len(nodes),
        kidl,
        s.count("Section"), s.count("InputCell"), s.count("TextCell"),
        s.count("<"), s.count(">"), s.count("comment"),
        ]
        dbutil.initDB("sqlite:///")
        nbc = notebook.NotebookController()
        session = nbc.session
        xmlutil.loadDBfromXML(session, s)
        u = notebook.NotebookUser(nbc, "userA")
        kidl = map(getattr, u.user.notebooks, ['children']*len(u.user.notebooks))
        kidl = map(len, kidl)
        kidl.sort()
        s2 = xmlutil.dumpDBtoXML(session)
        after = [
        len(session.query(Section).select()),
        len(session.query(InputCell).select()),
        len(session.query(TextCell).select()),
        len([n for n in nodes if n.parentID]),
        len([n for n in nodes if n.parent]),
        len(nodes),
        kidl,
        s2.count("Section"), s2.count("InputCell"), s2.count("TextCell"),
        s2.count("<"), s2.count(">"), s2.count("comment"),
        ]
        for b,a in zip(before, after):
            self.assertEquals(b,a)
        # print before, after
        err = (len(s)-len(s2))/(1.0*len(s))
        # print err
        self.assertAlmostEquals(err, 0, 2)
        # print len(s), len(s2)
    
    
        
        
        
    



