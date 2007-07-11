# encoding: utf-8
# -*- test-case-name: ipython1.test.test_notebook -*-
"""The main notebook system
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

from ipython1.notebook import nodes, dbutil


#-------------------------------------------------------------------------------
# Notebook Interface
#-------------------------------------------------------------------------------

class INotebook(zi.Interface):
    """The IPython Notebook Interface"""


class Notebook(object):
    """The basic IPython Notebook object"""
    
    def __init__(self, db, baseNodeID=None):
        self._db = db
        
        self.classes = nodes.classes
        
        self._connect()
        if baseNodeID is None:
            ids = self.getNodeIDs()
            id = max(ids)+1
            self._db.tables['registry'].insert(values=(id, 'Node')).execute()
            n = nodes.Node(id)
            cstr = ','.join(map(str, [str(c.id) for c in n.children]))
            self._db.tables['Node'].insert(values=(n.id, 0, 
                ';'.join(n.tags), n.dateCreated, n.dateModified, ''
                )).execute()
            self.baseNode = self.queries['Node'].selectone_by(id=id)
        else:
            self.baseNode = self.queries['Node'].selectfirst_by(id=baseNodeID)
    
    def getNodeIDs(self):
        l = [r.id for r in self.queries['registry']]
        if not l:
            l = [0]
        return l
    
    def _connect(self):
        self.session = sqla.create_session()
        self.queries = {}
        sqla.orm.clear_mappers()
        for c in self.classes:
            klass = getattr(nodes, c)
            sqla.mapper(klass, self._db.tables[c])
            self.queries[c] = self.session.query(klass)
        sqla.mapper(dbutil.RegistryEntry, self._db.tables['registry'])
        self.queries['registry'] = self.session.query(dbutil.RegistryEntry)
        




