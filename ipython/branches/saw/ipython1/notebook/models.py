from sqlalchemy import *
import datetime
# Setup the global unbound metadata.

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
    # Column('headID', Integer, ForeignKey('nodes.nodeID')),
    # Column('tailID', Integer, ForeignKey('nodes.nodeID')),
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
    Column('username', String(64)),
    Column('email', String(64)),
    Column('dateCreated', DateTime),
    Column('dateModified', DateTime)
)

# Mappers
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
    
class Cell(Node):
    pass

class InputCell(Cell):
    
    def __init__(self, input='', output='', comment='', parent=None):
        super(InputCell, self).__init__(comment, parent)
        self.input = input
        self.output = output

class TextCell(Cell):
    
    def __init__(self, textData='', comment='', parent=None):
        super(TextCell, self).__init__(comment, parent)
        self.textData = textData

class User(Timestamper):
    def __init__(self, username='', email=''):
        super(User, self).__init__()
        self.username = username
        self.email = email

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
        # 'head': relation(Node,
        #     primaryjoin=nodesTable.c.nodeID==sectionsTable.c.headID,
        #     foreign_keys=[sectionsTable.c.headID],
        #     uselist=False),
        # 'tail': relation(Node,
        #     primaryjoin=nodesTable.c.nodeID==sectionsTable.c.tailID,
        #     foreign_keys=[sectionsTable.c.tailID],
        #     uselist=False),
    }
)
userMapper = mapper(User, usersTable,
    properties={
        'nodes':relation(Node, 
        primaryjoin=usersTable.c.userID==nodesTable.c.userID,
        cascade="all, delete-orphan", backref='user')
        
    }
)