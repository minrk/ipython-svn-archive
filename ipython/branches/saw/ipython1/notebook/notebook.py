# encoding: utf-8
# -*- test-case-name: ipython1.test.test_notebook -*-
"""The main notebook server system
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

import zope.interface as zi
import sqlalchemy as sqla

from ipython1.kernel.error import NotFoundError
from ipython1.notebook import models, dbutil, xmlutil


#-------------------------------------------------------------------------------
# Notebook Server
#-------------------------------------------------------------------------------

class INotebookServer(zi.Interface):
    """The IPython Notebook Server Interface"""
    
    def addUser(uname, email):
        """add a user with `uname` and `email`"""
    
    def getUser(**selectflags):
        """get a User by flags passed to selectone_by"""
    
    def dropUser(**selectflags):
        """Drop a User by flags passed to selectone_by"""
    
    def addNode(node, parent, indices=None):
        """add a Node to """
    
    def getNode(**selectflags):
        """get a Node by flags passed to selectone_by"""
    
    def dropNode(**selectflags):
        """Drop a Node by flags passed to selectone_by"""
    
    def addRootSection(user, title):
        """create a root(parentless) Section for `user` with `title`"""
    
    def loadSectionFromXML(xmlstr):
        """load a section into the db from an xml file"""
    

class NotebookServer(object):
    """The basic IPython Notebook Server object"""
    zi.implements(INotebookServer)
    
    def __init__(self, metadata, session=None):
        self.db = metadata
        if session is None:
            session = sqla.create_session()
        self.session = session
        self.users = session.query(models.User)
        self.nodes = session.query(models.Node)
        self.sections = session.query(models.Section)
        self.cells = session.query(models.Cell)
    
    def getUser(self, **selectflags):
        try:
            return self.users.selectone_by(**selectflags)
        except:
            raise NotFoundError("No Such User: %s"%selectflags)
    
    def addUser(self, uname, email):
        try:
            return dbutil.createUser(self.session, uname, email)
        except:
            raise AssertionError("Username %s is taken!"%uname)
        
    def dropUser(self, **selectflags):
        u = self.getUser(**selectflags)
        dbutil.dropObject(self.session, u)
    
    def getNode(self, **selectflags):
        try:
            return self.nodes.selectone_by(**selectflags)
        except:
            raise NotFoundError("No Such Node: %s"%selectflags)
    
    def dropNode(self, **selectflags):
        n = self.getNode(**selectflags)
        dbutil.dropObject(self.session, n)
    
    def addNode(self, node, parent, indices=None):
        """add a cell to user's section with title `nbtitle`.  Indices
        can be None, int, list of ints.
        If None or int: add to nb.root at end or index.
        If list of ints: cascading add - add to nb.root[l[0]][l[1]]...
            at index indices[-1].
            each cell on the walk must be a MultiCell.
        """
        if indices is None or isinstance(indices,int):
            return dbutil.addChild(self.session, node, parent, indices)
        else:
            for i in indices[:-1]:
                parent = parent[i]
            return dbutil.addChild(self.session, node, parent, indices[-1])
    
    def addRootSection(self, user, title):
        root = dbutil.createRootSection(self.session, user, title)
        return root
    
    def loadSectionFromXML(self, xmlstr):
        sec = xmlutil.SectionFromXML(self.session, xmlstr)
        return sec
    
    




