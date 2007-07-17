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
            return self.users.selectone_by(username=user)
    
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
        return self.notebooks.selectone_by(username=uname, title=title)
    
    def addNotebook(self, user, title):
        u = self.getUser(user)
        existlist = self.notebooks.select_by(username=u.username, title=title)
        assert not existlist, "User '%s' already hase notebook ''%s"%(
            u.username, title)
        
        nb = dbutil.createNotebook(self.session, u, title)
        return nb
    
    def dropNotebook(self, user, title):
        nb = self.getNotebook(user, title)
        dbutil.dropObject(self.session, nb)
    




