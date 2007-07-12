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
from ipython1.notebook import nodes


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
        # sqla.Column("parent", sqla.Integer),
        sqla.Column("tags", bigstr),
        sqla.Column("dateCreated", smallstr),
        sqla.Column("dateModified", smallstr),
        sqla.Column("children", bigstr))
    sqla.Table("TextCell", db, 
        sqla.Column("id", sqla.Integer, primary_key=True, unique=True),
        # sqla.Column("parent", sqla.Integer),
        sqla.Column("tags", bigstr),
        sqla.Column("dateCreated", smallstr),
        sqla.Column("dateModified", smallstr),
        sqla.Column("text", bigstr),
        sqla.Column("format", smallstr))
    sqla.Table("IOCell", db, 
        sqla.Column("id", sqla.Integer, primary_key=True, unique=True),
        # sqla.Column("parent", sqla.Integer),
        sqla.Column("tags", bigstr),
        sqla.Column("dateCreated", smallstr),
        sqla.Column("dateModified", smallstr),
        sqla.Column("input", bigstr),
        sqla.Column("output", bigstr))
    sqla.Table("ImageCell", db, 
        sqla.Column("id", sqla.Integer, primary_key=True, unique=True),
        # sqla.Column("parent", sqla.Integer),
        sqla.Column("tags", bigstr),
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
    


#-------------------------------------------------------------------------------
# Adapters for Cells/Nodes to values for DB query
#-------------------------------------------------------------------------------

class IDBValues(zi.Interface):
    """An Interface for use in adapting cells and nodes to the values argument
    of a SQLAlchemy DB query."""
    pass

def dbvFromCell(cell):
    tags = ','.join(cell.tags)
    return (cell.id, tags, cell.dateCreated, cell.dateModified)

def dbvFromNode(node):
    kids = ','.join([str(c.id) for c in node.children])
    return dbvFromCell(node)+(node.kids,)

def dbvFromTextCell(cell):
    return dbvFromCell(cell)+(cell.text, cell.format)

def dbvFromIOCell(cell):
    return dbvFromCell(cell)+(cell.input, cell.output)

def dbvFromImageCell(cell):
    return dbvFromCell(cell)+(cell.image.tostring(),)

components.registerAdapter(dbvFromNode, nodes.INode, IDBValues)
components.registerAdapter(dbvFromTextCell, nodes.ITextCell, IDBValues)
components.registerAdapter(dbvFromIOCell, nodes.IIOCell, IDBValues)
components.registerAdapter(dbvFromImageCell, nodes.IImageCell, IDBValues)
