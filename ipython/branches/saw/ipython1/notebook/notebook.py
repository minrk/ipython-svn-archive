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

class INotebookController(zi.Interface):
    """The IPython Notebook Server Interface"""
    
    def connectUser(uname, email):
        """connect, and if necessary create, a user with `uname` and `email`"""
    
    def disconnectUser(userID):
        """disconnect a user by userID"""
    
    def dropUser(**selectflags):
        """Drop a User by flags passed to selectone_by"""
    
    def addNode(userID, parentID, node, indices=None):
        """add a Node to a parent Section, owned by userID"""
    
    def getNode(userID, **selectflags):
        """get a Node by flags passed to selectone_by, owned by userID"""
    
    def editNode(userID, nodeID, **options):
        """update attributes of node nodeID with keyword options"""
    
    def dropNode(userID, nodeID):
        """Drop a Node by nodeID, owned by userID"""
    
    def addRootSection(user, title):
        """create a root (parentless) Section for `user` with `title`"""
    
    def loadDBFromXML(xmlstr):
        """load the db from an xml file"""
    

class NotebookController(object):
    """The basic IPython Notebook Server object"""
    zi.implements(INotebookController)
    
    def __init__(self, session=None):
        if session is None:
            session = sqla.create_session()
        self.session = session
        self.userQuery = session.query(models.User)
        self.nodeQuery = session.query(models.Node)
        self.users = []
    
    def connectUser(self, usernameOrID, email=None):
        try:
            if email is None:
                if isinstance(usernameOrID, str):
                    user = self.userQuery.selectone_by(username=usernameOrID)
                elif isinstance(usernameOrID, int):
                    user = self.userQuery.selectone_by(userID=usernameOrID)
            else:
                user = self.userQuery.selectone_by(username=usernameOrID, email=email)
        except sqla.exceptions.InvalidRequestError:
            assert email is not None, "need to specify email to create new user"
            user = dbutil.createUser(self.session, usernameOrID, email)
        assert user.userID not in self.users, "User already connected"
        self.users.append(user.userID)
        return user
    
    def disconnectUser(self, userID):
        self.users.remove(userID)
    
    def dropUser(self, userID):
        assert userID in self.users, "You are not an active user!"
        u = self.userQuery.selectone_by(userID=userID)
        dbutil.dropObject(self.session, u)
    
    def getNode(self, userID, **selectflags):
        assert userID in self.users, "You are not an active user!"
        return self.nodeQuery.select_by(userID=userID, **selectflags)
    
    def addNode(self, userID, parentID, node, indices=None):
        """add a cell to user's section with title `nbtitle`.  Indices
        can be None, int, list of ints.
        If None or int: add to nb.root at end or index.
        If list of ints: cascading add - add to nb.root[l[0]][l[1]]...
            at index indices[-1].
            each cell on the walk must be a MultiCell.
        """
        assert userID in self.users, "You are not an active user!"
        # assert node.userID == userID, "You do not own this!"
        try:
            parent = self.nodeQuery.selectone_by(userID=userID, nodeID=parentID)
        except sqla.exceptions.InvalidRequestError:
            raise NotFoundError("No such Node, user:%i, node:%i"%(userID, parentID))
        assert isinstance(parent, models.Section), "parent must be a Section"
        
        if indices is None or isinstance(indices,int):
            return dbutil.addChild(self.session, node, parent, indices)
        else:
            for i in indices[:-1]:
                parent = parent[i]
            return dbutil.addChild(self.session, node, parent, indices[-1])
    
    def editNode(self, userID, nodeID, **options):
        assert userID in self.users, "You are not an active user!"
        node = self.nodeQuery.selectone_by(userID=userID, nodeID=nodeID)
        
        for k,v in options.iteritems():
            assert hasattr(node, k), "no such attr to edit"
            if k in ['parentID', 'nextID', 'previousID']:
                assert v is None or self.nodeQuery.select_by(nodeID=v)
            elif k == 'userID':
                assert v is None or self.userQuery.select_by(userID=v)
            setattr(node,k,v)
        node.touchModified()
        self.session.flush()
        return node
    
    def dropNode(self, userID, nodeID):
        assert userID in self.users, "You are not an active user!"
        nodes = self.getNode(userID, nodeID=nodeID)
        for node in nodes:
            dbutil.dropObject(self.session, node)
    
    def addRootSection(self, userID, title):
        assert userID in self.users, "You are not an active user!"
        u = self.userQuery.selectone_by(userID=userID)
        return dbutil.createRootSection(self.session, u, title)
    
    def loadDBFromXML(self, xmlstr):
        #
        raise NotImplementedError
        sec = xmlutil.SectionFromXML(self.session, xmlstr)
        return sec
    
    

class INotebookUser(zi.Interface):
    
    def getNode(**selectflags):
        """"""
    
    def dropNode(**selectflags):
        """"""
    
    def addNode(parentID, node, indices=None):
        """"""
    
    def editNode(nodeID, **options):
        """"""
    
    def addRootSection(title):
        """"""
    


class NotebookUser(object):
    """A User connected to the Notebook System"""
    
    def __init__(self, nbcontroller, usernameOrID, email=None):
        self.nbc = nbcontroller
        self.user = self.nbc.connectUser(usernameOrID, email)
    
    def __del__(self):
        try:
            self.disconnect()
        except:
            pass
    
    def disconnect(self):
        self.nbc.disconnectUser(self.user.userID)
    
    def getNode(self, **selectflags):
        return self.nbc.getNode(self.user.userID, **selectflags)
    
    def dropNode(self, nodeID):
        return self.nbc.dropNode(self.user.userID, nodeID)
    
    def addNode(self, parentID, node, indices=None):
        """add a node to user's Section with nodeID `parentID`.  Indices
        can be None, int, list of ints.
        If None or int: add to nb.root at end or index.
        If list of ints: cascading add - add to nb.root[l[0]][l[1]]...
            at index indices[-1].
            each cell on the walk must be a MultiCell.
        """
        return self.nbc.addNode(self.user.userID, parentID, node, indices)
    
    def editNode(self, nodeID, **options):
        return self.nbc.editNode(self.user.userID, nodeID, **options)
    
    def addRootSection(self, title):
        return self.nbc.addRootSection(self.user.userID, title)
    



