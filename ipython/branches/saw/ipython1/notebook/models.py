# encoding: utf-8
# -*- test-case-name: ipython1.test.test_notebook_models -*-
"""The main notebook Classes, serialization, and database system
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
from sqlalchemy import *
import datetime
# Setup the global unbound metadata.

#-------------------------------------------------------------------------------
# XML representations of notebook objects
#-------------------------------------------------------------------------------

def indent(s, n):
    """indent a multi-line string `s`, `n` spaces"""
    addline = 0
    if s[-1] == '\n':
        s = s[:-1]
        addline=1
    s = " "*n+s.replace("\n", "\n"+" "*n)
    return s +'\n'*addline

tformat = "%Y-%m-%d %H:%M:%S"

def XMLUser(u, justme=False):
    s  = "<userID>%i</userID>\n"%u.userID
    s += "<username>%s</username>\n"%u.username
    s += "<email>%s</email>\n"%u.email
    return "<User>\n%s</user>\n"%indent(s,2)
    
def XMLNodeBase(node):
    """The base of an XML representation of a Node"""
    s  = "<comment>%s</comment>\n"%(node.comment)
    for idname in ['nodeID', 'parentID', 'nextID', 'previousID', 'userID']:
        value = getattr(node, idname)
        if value is None:
            s += "<%s></%s>\n"%(idname, idname)
        else:
            s += "<%s>%i</%s>\n"%(idname, value, idname)
    s += "<dateCreated>%s</dateCreated>\n"%(node.dateCreated.strftime(tformat))
    s += "<dateModified>%s</dateModified>\n"%(node.dateModified.strftime(tformat))
    return s

def XMLSection(sec, justme=False):
    """Return an XML representation of a Section"""
    s  = XMLNodeBase(sec)
    s += "<title>%s</title>\n"%(sec.title)
    s += "<children>\n"
    if justme:
        childstr = ','.join([str(c.nodeID) for c in sec.children])
        s += indent(childstr,2)
    else:
        for i in range(len(sec.children)):
            s += indent(sec[i].xmlize(justme), 2)
    s += "</children>\n"
    return "<Section>\n%s</Section>\n"%indent(s,2)

def XMLTextCell(cell, justme=False):
    s  = XMLNodeBase(cell)
    s += "<textData>%s</textData>\n"%(cell.textData)
    return "<TextCell>\n%s</TextCell>\n"%indent(s,2)

def XMLInputCell(cell, justme=False):
    s  = XMLNodeBase(cell)
    s += "<input>%s</input>\n"%(cell.input)
    s += "<output>%s</output>\n"%(cell.output)
    return "<InputCell>\n%s</InputCell>\n"%indent(s,2)
    

#-------------------------------------------------------------------------------
# JSON Representations of Notebook Objects
#-------------------------------------------------------------------------------

def jsonStarter(obj):
    d = {}
    d['dateCreated'] = obj.dateCreated.strftime(tformat)
    d['dateModified'] = obj.dateModified.strftime(tformat)
    return d

def jsonifyUser(u, keepdict=False, justme=False):
    d = jsonStarter(u)
    d['userID'] = u.userID
    d['username'] = u.username
    d['email'] = u.email
    d['notebooks'] = [nb.title for nb in u.notebooks]
    if keepdict:
        return d
    return simplejson.dumps(d)

def jsonNode(n, keepdict=False, justme=False):
    d = jsonStarter(n)
    for key in ['cellID', 'parentID', 'nextID', 'previousID', 'comment']:
        d[key] = getattr(n, key)
    if keepdict:
        return d
    return simplejson.dumps(d)

def jsonifySection(sec, keepdict=False, justme=False):
    d = jsonNode(sec,True)
    d['title'] = sec.title
    if justme:
        d['children'] = [sec[i].cellID for i in range(len(sec.children))]
    else:
        d['children'] = [sec[i].jsonify(True,True)]
    if keepdict:
        return d
    return simplejson.dumps(d)

def jsonifyTextCell(tc, keepdict=False, justme=False):
    d = jsonNode(tc,True)
    d['textData'] = tc.textData
    if keepdict:
        return d
    return simplejson.dumps(d)

def jsonifyInputCell(ic, keepdict=False, justme=False):
    d = jsonNode(ic,True)
    d['input'] = ic.input
    d['output'] = ic.output
    if keepdict:
        return d
    return simplejson.dumps(d)


#-------------------------------------------------------------------------------
# SQLAlchemy Tables
#-------------------------------------------------------------------------------

metadata = MetaData()

# Tables

nodesTable = Table('nodes', metadata,
    Column('nodeID', Integer, primary_key=True),
    Column('dateCreated', DateTime),
    Column('dateModified', DateTime),
    Column('comment',String()),
    Column('userID', Integer, ForeignKey('users.userID')),
    Column('parentID', Integer, ForeignKey('nodes.nodeID')),
    Column('previousID', Integer, ForeignKey('nodes.nodeID')),
    Column('nextID', Integer, ForeignKey('nodes.nodeID')),
    Column('nodeType', String(32))
    )

sectionsTable = Table('sections', metadata,
    Column('nodeID', Integer, ForeignKey('nodes.nodeID'), primary_key=True),
    Column('headID', Integer, ForeignKey('nodes.nodeID')),
    Column('tailID', Integer, ForeignKey('nodes.nodeID')),
    Column('title',String())
)

inputCellsTable = Table('inputCells', metadata,
    Column('nodeID', Integer, ForeignKey('nodes.nodeID'), primary_key=True),
    Column('input', String()),
    Column('output', String()) 
)

textCellsTable = Table('textCells', metadata,
    Column('nodeID', Integer, ForeignKey('nodes.nodeID'), primary_key=True),
    Column('textData', String()),
)

usersTable = Table('users', metadata,
    Column('userID', Integer, primary_key=True),
    Column('username', String(64), unique=True),
    Column('email', String(64)),
    Column('dateCreated', DateTime),
    Column('dateModified', DateTime)
)

#-------------------------------------------------------------------------------
# SQLAlchemy Mappers
#-------------------------------------------------------------------------------

class Created(object):
    def __init__(self):
        self.dateCreated = datetime.datetime.now()

class Modified(object):
    def touchModified(self):
        self.dateModified = datetime.datetime.now()

class Timestamper(Created, Modified):
    def __init__(self):
        super(Timestamper, self).__init__()
        self.touchModified()

class Node(Timestamper):
    
    def __init__(self, comment='', parent=None):
        super(Node, self).__init__()
        self.comment = comment
        self.parent = parent
    
    # def _getNext(self, o):
    def insertBefore(self, c):
        """Insert a cell before this one."""
        assert not c is self, "Cannot insert Before/After self"
        assert self.parent is not None, "Cannot insert Before/After root"
        c.parent = self.parent
        c.user = self.user
        c.previousID = self.previousID
        if self.previous is not None:
            self.previous.nextID = c.nodeID
        self.previousID = c.nodeID
        c.nextID = self.nodeID
        # if self.previous is not None:
        #     self.previous.next = c
        # c.next = self
        
    def insertAfter(self, c):
        """Insert a cell after this one."""
        assert not c is self, "Cannot insert Before/After self"
        assert self.parent is not None, "Cannot insert Before/After root"
        c.parent = self.parent
        c.user = self.user
        ## by ID:
        c.nextID = self.nextID
        if self.next is not None:
            self.next.previousID = c.nodeID
        self.nextID = c.nodeID
        c.previousID = self.nodeID
        
        # c.next = self.next
        # self.next = c
    
    # def __str__(self):
    #     return self.xmlize()

class Section(Node):
    
    def __init__(self, title='', comment='', parent=None):
        super(Section, self).__init__(comment, parent)
        self.title = title
    
    def __getitem__(self, index):
        if index >= 0:
            c = self.children[0]
            for i in range(index):
                c = c.next
            return c
        else:
            c = self.children[-1]
            for i in range(-1-index):
                c = c.previous
            return c
    
    xmlize = XMLSection
    
    jsonify = jsonifySection

class Cell(Node):
    pass

class InputCell(Cell):
    
    def __init__(self, input='', output='', comment='', parent=None):
        super(InputCell, self).__init__(comment, parent)
        self.input = input
        self.output = output
    
    xmlize = XMLInputCell
    
    jsonify = jsonifyInputCell

class TextCell(Cell):
    
    def __init__(self, textData='', comment='', parent=None):
        super(TextCell, self).__init__(comment, parent)
        self.textData = textData
    
    xmlize = XMLTextCell
    
    jsonify = jsonifyTextCell

class User(Timestamper):
    def __init__(self, username='', email=''):
        super(User, self).__init__()
        self.username = username
        self.email = email
    
    xmlize = XMLUser
    
    jsonify = jsonifyUser

nodeJoin = polymorphic_union(
    {
        'inputCell':nodesTable.join(inputCellsTable),
        'textCell':nodesTable.join(textCellsTable),
        'section':nodesTable.join(sectionsTable, sectionsTable.c.nodeID==nodesTable.c.nodeID),
        'node':nodesTable.select(nodesTable.c.nodeType=='node')
    }, None, 'pjoin'
)

nodeMapper = mapper(Node, nodesTable, 
    select_table=nodeJoin, 
    polymorphic_on=nodeJoin.c.nodeType, 
    polymorphic_identity='node',
    properties = {
        'next': relation(Node,
            primaryjoin=nodesTable.c.nextID==nodesTable.c.nodeID,
            remote_side=[nodesTable.c.nodeID],
            uselist=False,
            # viewonly = True,
            backref=backref('previous',
                primaryjoin=nodesTable.c.previousID==nodesTable.c.nodeID,
                remote_side=[nodesTable.c.nodeID],
                viewonly = True,
                uselist=False)),
    }
)

cellJoin = polymorphic_union(
    {
        'inputCell':nodesTable.join(inputCellsTable),
        'textCell':nodesTable.join(textCellsTable),
        'cell':nodesTable.select(nodesTable.c.nodeType=='cell')
    }, None, 'pjoin'
)

cellMapper = mapper(Cell, nodesTable, 
    select_table=cellJoin, 
    polymorphic_on=cellJoin.c.nodeType, 
    polymorphic_identity='cell',
    inherits=nodeMapper
)

inputCellMapper = mapper(InputCell, inputCellsTable, inherits=cellMapper, polymorphic_identity='inputCell')
textCellMapper = mapper(TextCell, textCellsTable, inherits=cellMapper, polymorphic_identity='textCell')

sectionMapper = mapper(Section, sectionsTable, inherits = nodeMapper, polymorphic_identity='section',
    inherit_condition=sectionsTable.c.nodeID==nodesTable.c.nodeID,
    properties={
        'children': relation(
            Node,
            primaryjoin=nodesTable.c.parentID==nodesTable.c.nodeID,
            remote_side=[nodesTable.c.parentID],
            cascade='all, delete-orphan',
            order_by = [nodeJoin.c.previousID!=None, nodeJoin.c.nextID==None],
            # viewonly = True,
            backref=backref("parent",
                primaryjoin=nodesTable.c.parentID==nodesTable.c.nodeID,
                remote_side=[nodesTable.c.nodeID],
                uselist=False
                )
            ),
        # 'head': relation(Node,
        #     primaryjoin=sectionsTable.c.headID==nodesTable.c.nodeID,
        #     remote_side=[nodesTable.c.nodeID],
        #     # viewonly=True,
        #     uselist=False),
        # 'tail': relation(Node,
        #     primaryjoin=nodesTable.c.nodeID==sectionsTable.c.tailID,
        #     remote_side=[nodesTable.c.nodeID],
        #     # viewonly=True,
        #     uselist=False),
    }
)

userMapper = mapper(User, usersTable,
    properties={
        'nodes':relation(Node, 
        primaryjoin=usersTable.c.userID==nodesTable.c.userID,
        cascade="all, delete-orphan", backref='user'),
        'cells':relation(Cell,
        primaryjoin=usersTable.c.userID==nodesTable.c.userID,
        ),
        'notebooks':relation(Node,
        primaryjoin=and_(usersTable.c.userID==nodesTable.c.userID,
            nodesTable.c.parentID==None),
        )
    }
)
