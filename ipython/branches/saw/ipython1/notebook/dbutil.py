# encoding: utf-8
# -*- test-case-name: ipython1.test.test_notebook_dbutil -*-
"""The database utils for the notebook system
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

import os, sqlalchemy as sqla, zope.interface as zi

from twisted.python import components

from IPython.genutils import get_home_dir

from ipython1.config.api import resolveFilePath
from ipython1.kernel.error import DBError
from ipython1.notebook import models

metadata = models.metadata

#-------------------------------------------------------------------------------
# DB Utils
#-------------------------------------------------------------------------------

def connectDB(fname='ipnotebook.db', ipythondir=None):
    """
    BROKEN
    TO BE MOVED TO CONFIG SYSTEM
    
    Connect to aa notebook database, or attempt to create a new one
    if none is found.
    """
    f = resolveFilePath(fname, ipythondir)
    print f
    if f is None:
        print "Could not find DB, attempting to create new DB"
        err = DBError("Could not create DB")
        if ipythondir is not None:
            ipdir = ipythondir
        elif os.environ.get("IPYTHONDIR") is not None:
            ipdir = os.environ.get("IPYTHONDIR")
        else:
            try:
                home = get_home_dir()
                ipdir = home+'/.ipython'
                if not os.path.exists(ipdir):
                    ipdir = home
            except:
                raise err
        q = 'sqlite:///%s'%(ipdir+'/'+fname)
        # print q
        engine = sqla.create_engine(q)
        try:
            engine.connect()
        except sqla.exceptions.DBAPIError:
            raise err
        ipdb.connect(engine)
        ipdb.create_all()
        return ipdb
    else:
        engine = sqla.create_engine('sqlite:///%s'%(f))
        ipdb.connect(engine)
        # checkDB(DB)
        return ipdb

def initDB(dburi='sqlite://'):
    """create an engine, and connect our metadata object to it.  Then, 
    create our tables in the engine.  
    Defaults to an in-memory sqlite engine."""
    engine = sqla.create_engine(dburi)
    metadata.connect(engine)
    metadata.create_all()
    return metadata

def createUser(session, username, email):
    """create a user with username and email"""
    u = models.User(username, email)
    session.save(u)
    session.flush()
    return u

def dropObject(session, obj):
    """remove any object, and their dependents"""
    session.delete(obj)
    session.flush()
    
def createNotebook(session, user, title):
    """create a notebook for `user` with root node using `title`"""
    nb = models.Notebook()
    nb.user = user
    nb.root = models.Node(title)
    session.save(nb)
    session.flush()
    return nb

