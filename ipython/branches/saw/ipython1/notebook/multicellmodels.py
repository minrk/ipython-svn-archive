import datetime, zope.interface as zi
from sqlalchemy import *

# Setup the global unbound metadata.

metadata = MetaData()

# Tables

cellsTable = Table('cells', metadata,
    Column('cellID', Integer, primary_key=True),
    Column('dateCreated', DateTime),
    Column('dateModified', DateTime),
    Column('comment',String()),
    Column('parentID', Integer, ForeignKey('cells.cellID')),
    Column('previousID', Integer, ForeignKey('cells.cellID')),
    Column('nextID', Integer, ForeignKey('cells.cellID')),
    Column('cellType', String(32))
    )

multiCellsTable = Table('multiCells', metadata,
    Column('cellID', Integer, ForeignKey('cells.cellID'), primary_key=True),
    Column('title',String())
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
    Column('rootID', Integer, ForeignKey('cells.cellID')),    
)
    
usersTable = Table('users', metadata,
    Column('userID', Integer, primary_key=True),
    Column('username', String(64)),
    Column('email', String(64)),
    Column('dateCreated', DateTime),
    Column('dateModified', DateTime)
)

# interface classes for adaptation
class IUser(zi.Interface):
    """the interface for a user"""
    pass

class INotebook(zi.Interface):
    """the interface for a notebook"""
    pass

class ICell(zi.Interface):
    """the interface for a cell"""
    pass

class IMultiCell(ICell):
    """The interface for a MultiCell"""
    pass

class ITextCell(ICell):
    """the interface for a text cell"""
    pass

class IInputCell(ICell):
    """the interface for a text cell"""
    pass

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

class Cell(Timestamper):
    zi.implements(ICell)
    
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

class MultiCell(Cell):
    zi.implements(IMultiCell)
    
    def __init__(self, title='', comment='', parent=None):
        super(MultiCell, self).__init__(comment, parent)
        self.title = title
    
    def _getFirst(self):
        c = self.children[0]
        while c.previous is not None:
            c = c.previous
        return c
    
    def _getLast(self):
        c = self.children[-1]
        while c.next is not None:
            c = c.next
        return c
    
    def __getitem__(self, index):
        if index >= 0:
            c = self._getFirst()
            for i in range(index):
                c = c.next
            return c
        else:
            c = self._getLast()
            for i in range(-1-index):
                c = c.previous
            return c
    

class InputCell(Cell):
    zi.implements(IInputCell)
    
    def __init__(self, input='', output='', comment='', parent=None):
        super(InputCell, self).__init__(comment, parent)
        self.input = input
        self.output = output

class TextCell(Cell):
    zi.implements(ITextCell)
    
    def __init__(self, textData='', comment='', parent=None):
        super(TextCell, self).__init__(comment, parent)
        self.textData = textData

class User(Timestamper):
    zi.implements(IUser)
    def __init__(self, username='', email=''):
        super(User, self).__init__()
        self.username = username
        self.email = email

class Notebook(Timestamper):
    zi.implements(INotebook)
    def __init__(self):
        super(Notebook, self).__init__()


cellJoin = polymorphic_union(
    {
        'inputCell':cellsTable.join(inputCellsTable),
        'textCell':cellsTable.join(textCellsTable),
        'multiCell':cellsTable.join(multiCellsTable),
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
            remote_side=[cellsTable.c.cellID],
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
multiCellMapper = mapper(MultiCell, multiCellsTable, inherits=cellMapper, polymorphic_identity='multiCell',
    properties={
        'children': relation(
            Cell,
            primaryjoin=cellsTable.c.parentID==cellsTable.c.cellID,
            cascade='all, delete-orphan',
            backref=backref("parent",
                primaryjoin=cellsTable.c.parentID==cellsTable.c.cellID,
                remote_side=[cellsTable.c.cellID],
                uselist=False
                )
            ),
    }
)

userMapper = mapper(User, usersTable,
    properties=dict(notebooks=relation(Notebook, 
        cascade="all, delete-orphan", backref='user')))
notebookMapper = mapper(Notebook, notebooksTable,
    properties=dict(root=relation(MultiCell, uselist=False)))



