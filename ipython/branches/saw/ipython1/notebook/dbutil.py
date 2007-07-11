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
from ipython1.config.api import resolveFilePath
from ipython1.kernel.error import DBError
from IPython.genutils import get_home_dir


#-------------------------------------------------------------------------------
# DB Utils
#-------------------------------------------------------------------------------

def connectDB(fname='ipnotebook.db', ipythondir=None):
    """Connect to aa notebook database, or attempt to create a new one
    if none is found.
    """
    f = resolveFilePath(fname, ipythondir)
    global DB
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
        q = 'sqlite://%s'%(ipdir+'/'+fname)
        print q
        engine = sqla.create_engine('sqlite:///%s'%(ipdir+'/'+fname))
        try:
            engine.connect()
        except sqla.exceptions.DBAPIError:
            raise err
        DB = sqla.MetaData()
        DB.connect(engine)
        initDB(DB)
        return DB
    else:
        engine = sqla.create_engine('sqlite:///%s'%(f))
        engine.connect()
        DB = sqla.MetaData()
        DB.connect(engine)
        checkDB(DB)
        return DB

def initDB(db):
    """initialize the database, dropping any existing data"""
    db.drop_all()
    bigstr = sqla.String(128)
    smallstr = sqla.String(32)
    sqla.Table("registry", db, 
        sqla.Column("id", sqla.Integer, primary_key=True, unique=True),
        sqla.Column("className", smallstr))
    sqla.Table("Node", db, 
        sqla.Column("id", sqla.Integer, primary_key=True, unique=True),
        sqla.Column("parent", sqla.Integer),
        sqla.Column("flags", bigstr),
        sqla.Column("dateCreated", smallstr),
        sqla.Column("dateModified", smallstr),
        sqla.Column("children", bigstr))
    sqla.Table("TextCell", db, 
        sqla.Column("id", sqla.Integer, primary_key=True, unique=True),
        sqla.Column("parent", sqla.Integer),
        sqla.Column("flags", bigstr),
        sqla.Column("dateCreated", smallstr),
        sqla.Column("dateModified", smallstr),
        sqla.Column("text", bigstr),
        sqla.Column("format", smallstr))
    sqla.Table("IOCell", db, 
        sqla.Column("id", sqla.Integer, primary_key=True, unique=True),
        sqla.Column("parent", sqla.Integer),
        sqla.Column("flags", bigstr),
        sqla.Column("dateCreated", smallstr),
        sqla.Column("dateModified", smallstr),
        sqla.Column("input", bigstr),
        sqla.Column("output", bigstr))
    sqla.Table("ImageCell", db, 
        sqla.Column("id", sqla.Integer, primary_key=True, unique=True),
        sqla.Column("parent", sqla.Integer),
        sqla.Column("flags", bigstr),
        sqla.Column("dateCreated", smallstr),
        sqla.Column("dateModified", smallstr)
        , sqla.Column("image", bigstr))
    db.create_all()

def checkDB(db):
    """check if the database is appropriate"""
    pass


class RegistryEntry(object):
    """A registry object for use in mapping"""
    def __repr__(self):
        return "(%i, %s)"%(self.id, self.klass)
    
