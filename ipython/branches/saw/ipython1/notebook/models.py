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

def XMLUser(u):
    s  = "<userID>%i</userID>\n"%u.userID
    s += "<username>%s</username>\n"%u.username
    s += "<email>%s</email>\n"%u.email
    return "<User>\n%s</user>\n"%indent(s,2)
    
def XMLNodeBase(node):
    """The base of an XML representation of a Node"""
    s  = "<nodeID>%i</nodeID>\n"%node.nodeID
    s += "<userID>%i</userID>\n"%node.user.userID
    s += "<parentID>%i</parentID>\n"%node.parentID
    s += "<previousID>%i</previousID>\n"%node.previousID
    s += "<nextID>%i</nextID>\n"%node.nextID
    s += "<comment>%s</comment>\n"%(node.comment)
    s += "<dateCreated>%s</dateCreated>\n"%(node.dateCreated.strftime(tformat))
    s += "<dateModified>%s</dateModified>\n"%(node.dateModified.strftime(tformat))
    return s

def XMLSection(sec):
    """Return an XML representation of a Section"""
    s  = XMLNodeBase(sec)
    s += "<title>%s</title>\n"%(sec.title)
    for i in range(len(sec.children)):
        s += indent(sec[i].xmlize(), 2)
    return "<Section>\n%s</Section>\n"%indent(s,2)

def XMLTextCell(cell):
    s  = XMLNodeBase(cell)
    s += "<textData>%s</textData>\n"%(cell.textData)
    return "<TextCell>\n%s</TextCell>\n"%indent(s,2)

def XMLInputCell(cell):
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

def jsonifyUser(u):
    d = jsonStarter(u)
    d['userID'] = u.userID
    d['username'] = u.username
    d['email'] = u.email
    d['notebooks'] = [nb.title for nb in u.notebooks]
    return simplejson.dumps(d)

def jsonNode(n):
    d = jsonStarter(n)
    for key in ['cellID', 'parentID', 'nextID', 'previousID', 'comment']:
        d[key] = getattr(n, key)
    return d

def jsonifySection(sec):
    d = jsonNode(sec)
    d['title'] = sec.title
    d['children'] = [sec[i].cellID for i in range(len(sec.children))]
    return simplejson.dumps(d)

def jsonifyTextCell(tc):
    d = jsonNode(tc)
    d['textData'] = tc.textData
    return simplejson.dumps(d)

def jsonifyInputCell(ic):
    d = jsonNode(ic)
    d['input'] = ic.input
    d['output'] = ic.output
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

    def insertBefore(self, c):
        """Insert a cell before this one."""
        c.parent = self.parent
        c.user = self.user
        c.previous = self.previous
        c.next = self
        
    def insertAfter(self, c):
        """Insert a cell after this one."""
        c.parent = self.parent
        c.user = self.user
        c.next = self.next
        c.previous = self

class Section(Node):
    
    def __init__(self, title='', comment='', parent=None):
        super(Section, self).__init__(comment, parent)
        self.title = title
    
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
        'next': relation(Node,
            primaryjoin=nodesTable.c.nextID==nodesTable.c.nodeID,
            uselist=False,
            backref=backref('previous',
                primaryjoin=nodesTable.c.previousID==nodesTable.c.nodeID,
                remote_side=[nodesTable.c.nodeID],
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
            cascade='all, delete-orphan',
            backref=backref("parent",
                primaryjoin=nodesTable.c.parentID==nodesTable.c.nodeID,
                remote_side=[nodesTable.c.nodeID],
                uselist=False
                )
            ),
        'head': relation(Node,
            primaryjoin=nodesTable.c.nodeID==sectionsTable.c.headID,
            foreign_keys=[sectionsTable.c.headID],
            uselist=False),
        'tail': relation(Node,
            primaryjoin=nodesTable.c.nodeID==sectionsTable.c.tailID,
            foreign_keys=[sectionsTable.c.tailID],
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
