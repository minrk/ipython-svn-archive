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
    s += "<dateCreated>%s</dateCreated>\n"%(u.dateCreated.strftime(tformat))
    s += "<dateModified>%s</dateModified>\n"%(u.dateModified.strftime(tformat))
    s += "<justme>"+ '1'*justme + "</justme>\n"
    s += "<Notebooks>"
    if justme:
        nbstr = ','.join([str(c.nodeID) for c in u.notebooks])
        s += indent(nb,2)
    else:
        s += '\n'
        for nb in u.notebooks:
            s += indent(nb.xmlize(justme=False), 2)
    s += "</Notebooks>\n"
    s += "<Nodes>"
    nstr = ','.join([str(c.nodeID) for c in u.nodes])
    s += nstr
    s += "</Nodes>\n"
    return "<User>\n%s</User>\n"%indent(s,2)
    
def XMLNodeBase(node, justme):
    """The base of an XML representation of a Node"""
    s  = "<comment>%s</comment>\n"%(node.comment)
    for idname in ['nodeID', 'nextID','previousID', 'parentID', 'userID']:
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
    s  = XMLNodeBase(sec, justme)
    s += "<justme>"+ '1'*justme + "</justme>\n"
    s += "<title>%s</title>\n"%(sec.title)
    for idname in ['headID','tailID']:
        value = getattr(sec, idname)
        if value is None:
            s += "<%s></%s>\n"%(idname, idname)
        else:
            s += "<%s>%i</%s>\n"%(idname, value, idname)
    s += "<children>"
    if justme:
        kids = ','.join([str(sec[i].nodeID) for i in range(len(sec.children))])
        s += kids
    else:
        s += '\n'
        for i in range(len(sec.children)):
            s += indent(sec[i].xmlize(justme), 2)
    s += "</children>\n"
    return "<Section>\n%s</Section>\n"%indent(s,2)

def XMLTextCell(cell, justme=False):
    s  = XMLNodeBase(cell, justme)
    s += "<textData>%s</textData>\n"%(cell.textData)
    return "<TextCell>\n%s</TextCell>\n"%indent(s,2)

def XMLInputCell(cell, justme=False):
    s  = XMLNodeBase(cell, justme)
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
    for key in ['cellID', 'parentID', 'nextID', 'comment']:
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
        if getattr(self, 'parent', None) is not None:
            self.parent.touchModified()

class Timestamper(Created, Modified):
    def __init__(self):
        super(Timestamper, self).__init__()
        self.touchModified()

class Node(Timestamper):
    
    def __init__(self, comment='', parent=None):
        super(Node, self).__init__()
        self.comment = comment
        self.parent = parent
    
    def _getNext(self): return self._next
    
    def _setNext(self, n):
        if n is not None:
            n.previousID = self.nodeID
        self._next = n
    
    next = property(_getNext, _setNext)
    
    def _getPrevious(self): return self._previous
    
    def _setPrevious(self, n):
        if n is not None:
            n.next = self
    
    previous = property(_getPrevious, _setPrevious)
    
    def insertBefore(self, c):
        """Insert a cell before this one."""
        assert self.parent is not None, "Cannot insert Before/After root"
        assert c not in self.parent.children, "Already in Children"
        c.parent = self.parent
        c.user = self.user
        c.previous = self.previous
        c.next = self
        self.touchModified()
        c.touchModified()
        
    def insertAfter(self, c):
        """Insert a cell after this one."""
        assert not c is self, "Cannot insert Before/After self"
        assert c not in self.parent.children, "Already in Children"
        c.parent = self.parent
        c.user = self.user
        c.next = self.next
        self.next = c
        self.touchModified()
        c.touchModified()
    

class Section(Node):
    
    def __init__(self, title='', comment='', parent=None):
        super(Section, self).__init__(comment, parent)
        self.title = title
    
    def _getChildren(self):
        return [self[i] for i in range(len(self._children))]
    
    def _setChildren(self, children):
        self._children = children
    
    children = property(_getChildren, _setChildren)
    
    def __getitem__(self, index):
        if index >= 0:
            c = self.head
            for i in range(index):
                c = c.next
            return c
        else:
            c = self.tail
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
        '_next': relation(Node,
            primaryjoin=nodesTable.c.nextID==nodesTable.c.nodeID,
            remote_side=[nodesTable.c.nodeID],
            uselist=False,
            backref=backref('_previous',
                primaryjoin=nodesTable.c.nextID==nodesTable.c.nodeID,
                remote_side=[nodesTable.c.nextID],
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
        '_children': relation(
            Node,
            primaryjoin=nodesTable.c.parentID==nodesTable.c.nodeID,
            remote_side=[nodesTable.c.parentID],
            cascade='all, delete-orphan',
            backref=backref("parent",
                primaryjoin=nodesTable.c.parentID==nodesTable.c.nodeID,
                remote_side=[nodesTable.c.nodeID],
                uselist=False
                )
            ),
        'head': relation(Node,
            primaryjoin=and_(sectionsTable.c.headID==nodesTable.c.nodeID),
            remote_side=[nodesTable.c.nodeID],
            viewonly = True,
            uselist=False),
        'tail': relation(Node,
            primaryjoin=and_(sectionsTable.c.tailID==nodesTable.c.nodeID),
            remote_side=[nodesTable.c.nodeID],
            viewonly = True,
            uselist=False),
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
