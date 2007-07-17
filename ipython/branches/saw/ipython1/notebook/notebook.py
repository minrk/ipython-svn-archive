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

from twisted.python import components

from ipython1.kernel.error import DBError, NotFoundError
from ipython1.notebook import multicellmodels as models, dbutil


#-------------------------------------------------------------------------------
# Notebook Server
#-------------------------------------------------------------------------------

class INotebookServer(zi.Interface):
    """The IPython Notebook Server Interface"""


class NotebookServer(object):
    """The basic IPython Notebook Server object"""
    
    def __init__(self, metadata, session=None):
        self.db = metadata
        if session is None:
            session = sqla.create_session()
        self.session = session
        self.users = session.query(models.User)
        self.notebooks = session.query(models.Notebook)
    
    def getUser(self, user):
        if isinstance(user, models.User):
            return user
        else:
            try:
                return self.users.selectone_by(username=user)
            except:
                raise NotFoundError("No Such User: %s"%user)
    
    def addUser(self, uname, email):
        existlist = self.users.select_by(username=uname)
        assert not existlist, "Username '%s' already in use"%uname
        u = dbutil.createUser(self.session, uname, email)
        return u
        
    def dropUser(self, user):
        u = self.getUser(user)
        dbutil.dropObject(self.session, u)
    
    def getNotebook(self, user, title):
        uname = self.getUser(user).username
        try:
            return self.notebooks.selectone_by(username=uname, title=title)
        except:
            raise NotFoundError("No Such Notebook: %s"%title)
    
    def addNotebook(self, user, title):
        u = self.getUser(user)
        existlist = self.notebooks.select_by(username=u.username, title=title)
        assert not existlist, "User '%s' already hase notebook '%s'"%(
            u.username, title)
        nb = dbutil.createNotebook(self.session, u, title)
        return nb
    
    def dropNotebook(self, user, title):
        nb = self.getNotebook(user, title)
        dbutil.dropObject(self.session, nb)
    
    def addCell(self, cell, user, nbtitle, indices=None):
        """add a cell to user's notebook with title `nbtitle`.  Indices
        can be None, int, list of ints.  
        If None or int: add to nb.root at end or index.
        If list of ints: cascading add - add to nb.root[l[0]][l[1]]...
            at index indices[-1].
            each cell on the walk must be a MultiCell.
        """
        nb = self.getNotebook(user, nbtitle)
        
        if indices is None or isinstance(indices,int):
            return dbutil.addChild(self.session, cell, nb.root)
        else:
            mc = nb.root
            # walk down to correct MultiCell
            for i in indices[:-1]:
                mc = mc[i]
            return dbutil.addChild(self.session, cell, mc, indices[-1])
    




