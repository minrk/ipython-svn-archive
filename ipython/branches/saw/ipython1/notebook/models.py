import datetime
from sqlalchemy import *

# Setup the global unbound metadata.

metadata = MetaData()

# Tables

nodesTable = Table('nodes', metadata,
    Column('nodeID', Integer, primary_key=True),
    Column('parentID', Integer, ForeignKey('nodes.nodeID')),
    Column('previousID', Integer, ForeignKey('nodes.nodeID')),
    Column('nextID', Integer, ForeignKey('nodes.nodeID')),
    Column('title',String())
)

cellsTable = Table('cells', metadata,
    Column('cellID', Integer, primary_key=True),
    Column('dateCreated', DateTime),
    Column('dateModified', DateTime),
    Column('comment',String()),
    Column('nodeID', Integer, ForeignKey('nodes.nodeID')),
    Column('previousID', Integer, ForeignKey('cells.cellID')),
    Column('nextID', Integer, ForeignKey('cells.cellID')),
    Column('cellType', String(32))
    )

inputCellsTable = Table('inputCells', metadata,
    Column('cellID', Integer, ForeignKey('cells.cellID'), primary_key=True),
    Column('input', String()),
    Column('output', String()) 
)

textCellsTable = Table('textCells', metadata,
    Column('cellID', Integer, ForeignKey('cells.cellID'), primary_key=True),
    Column('textData', String()),
)

notebooksTable = Table('notebooks', metadata,
    Column('notebookID', Integer, primary_key=True),
    Column('userID', Integer, ForeignKey('users.userID')),
    Column('dateCreated', DateTime),
    Column('dateModified', DateTime),
    Column('rootID', Integer, ForeignKey('nodes.nodeID')),    
)
    
usersTable = Table('users', metadata,
    Column('userID', Integer, primary_key=True),
    Column('username', String(64)),
    Column('email', String(64)),
    Column('dateCreated', DateTime),
    Column('dateModified', DateTime)
)

# Mappers

class Node(object):
    
    def __init__(self, title, parent=None):
        self.title = title
        self.parent = None
    
    def insertBefore(self, n):
        """Insert a node before this one."""
        n.parent = self.parent
        n.previous = self.previous
        n.next = self
    
    def insertAfter(self, n):
        """Insert a node after this one."""
        n.parent = self.parent
        n.next = self.next
        n.previous = self
    

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

class Cell(Timestamper):
    
    def __init__(self, comment='', parent=None):
        super(Cell, self).__init__()
        self.comment = comment
        self.parent = parent

    def insertBefore(self, c):
        """Insert a cell before this one."""
        c.parent = self.parent
        c.previous = self.previous
        c.next = self
        
    def insertAfter(self, c):
        """Insert a cell after this one."""
        c.parent = self.parent
        c.next = self.next
        c.previous = self

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

class Notebook(Timestamper):
    
    def __init__(self):
        super(Notebook, self).__init__()


nodeMapper = mapper(Node, nodesTable,
    properties={
        'childrenCells': relation(
            Cell,
            cascade='all, delete-orphan',
            backref=backref('parent')),
        'childrenNodes': relation(
            Node,
            primaryjoin=nodesTable.c.parentID==nodesTable.c.nodeID,
            cascade="all",
            backref=backref("parent",
                    primaryjoin=nodesTable.c.parentID==nodesTable.c.nodeID,
                    remote_side=[nodesTable.c.nodeID],
                    uselist=False)),
        'next': relation(
            Node,
            primaryjoin=nodesTable.c.nextID==nodesTable.c.nodeID,
            uselist=False,
            backref=backref('previous',
                    primaryjoin=nodesTable.c.previousID==nodesTable.c.nodeID,
                    remote_side=[nodesTable.c.nodeID],
                    uselist=False))
    }
)
    
cellJoin = polymorphic_union(
    {
        'inputCell':cellsTable.join(inputCellsTable),
        'textCell':cellsTable.join(textCellsTable),
        'cell':cellsTable.select(cellsTable.c.cellType=='cell')
    }, None, 'pjoin')
cellMapper = mapper(Cell, cellsTable, 
    select_table=cellJoin, 
    polymorphic_on=cellJoin.c.cellType, 
    polymorphic_identity='cell',
    properties = {
        'next': relation(
            Cell,
            primaryjoin=cellsTable.c.nextID==cellsTable.c.cellID,
            uselist=False,
            backref=backref('previous',
                primaryjoin=cellsTable.c.previousID==cellsTable.c.cellID,
                remote_side=[cellsTable.c.cellID],
                uselist=False)
        )
    }
)
inputCellMapper = mapper(InputCell, inputCellsTable, inherits=cellMapper, polymorphic_identity='inputCell')
textCellMapper = mapper(TextCell, textCellsTable, inherits=cellMapper, polymorphic_identity='textCell')

userMapper = mapper(User, usersTable,
    properties=dict(notebooks=relation(Notebook, 
        cascade="all, delete-orphan", backref='user')))
notebookMapper = mapper(Notebook, notebooksTable,
    properties=dict(root=relation(Node, uselist=False)))



