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

from ipython1.notebook import models, dbutil


#-------------------------------------------------------------------------------
# Notebook Interface
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
        self.nodes = session.query(models.Node)
    
    def getUser(self, uname):
        return self.users.selectone_by(username=uname)
    
    def addUser(self, uname, email):
        existlist = self.users.select_by(username=uname)
        assert not existlist, "Username '%s' already in use"%uname
        u = dbutil.addUser(self.session, uname, email)
        return u
        
    def dropUser(self, uname):
        u = self.getUser(uname)
        dbutil.dropObject(self.session, u)
    
    def addNotebook(self, uname, title):
        user = self.getUser(uname)
        nb = dbutil.createNotebook(self.session, user, title)
        return nb
    
    def dropNotebook(self, uname, title):
        user = self.getUser(uname)
        nb = self.notebooks.select_by(userID=user.userID, title=title)
        dbutil.dropObject(nb)
    
