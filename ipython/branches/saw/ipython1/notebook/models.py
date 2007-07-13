import datetime
from sqlalchemy import *

db = create_engine('sqlite:///notebook.db')

metadata = BoundMetaData(db)

metadata.engine.echo = True

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
    Column('nextID', Integer, ForeignKey('cells.cellID'))
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
    Column('username', String(40)),
    Column('email', String(40)),
    Column('dateCreated', DateTime),
    Column('dateModified', DateTime)
)

def createTables():
    nodesTable.create()
    cellsTable.create()
    inputCellsTable.create()
    textCellsTable.create()
    notebooksTable.create()
    usersTable.create()

# Mappers

class Node(object):
    pass

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
    
    def __init__(self):
        super(Cell, self).__init__()

class InputCell(Cell):
    
    def __init__(self):
        super(InputCell, self).__init__()

class TextCell(Cell):

    def __init__(self):
        super(TextCell, self).__init__()

class User(Timestamper):
    
    def __init__(self):
        super(User, self).__init__()

class Notebook(Timestamper):
    
    def __init__(self):
        super(Notebook, self).__init__()

def createMappers():
    nodeMapper = mapper(Node, nodesTable,
        properties=dict(inputCells=relation(InputCell, 
                            cascade="all, delete-orphan"),
                        textCells=relation(TextCell, 
                            cascade="all, delete-orphan"),
                        children=relation(Node,
                            cascade="all", backref='parent', 
                                primaryjoin=nodesTable.c.nodeID==nodesTable.c.parentID)))
    cellMapper = mapper(Cell, cellsTable)
    inputCellMapper = mapper(InputCell, inputCellsTable, inherits=cellMapper)
    textCellMapper = mapper(TextCell, textCellsTable, inherits=cellMapper)
    userMapper = mapper(User, usersTable,
        properties=dict(notebooks=relation(Notebook, 
            cascade="all, delete-orphan", backref='user')))
    notebookMapper = mapper(Notebook, notebooksTable,
        properties=dict(root=relation(Node, uselist=False)))

    
# Initialization

createTables()
createMappers()

# Actually do some transactions

session = create_session()

def createUser(session):
    # Create user
    u = User()
    u.username = 'bgranger'
    u.email = 'ellisonbg@gmail.com'
    session.save(u)
    session.flush()
    return u
    
def createNotebook(session, user):
    nb = Notebook()
    nb.user = user
    session.save(nb)
    session.flush()
    return nb

u = createUser(session)
nb = createNotebook(session, u)

# node = Node()
# nb.root = node
# ic = InputCell()
# ic.input = 'import time'
# node.inputCells.append(ic)
# session.save(node, ic)
# session.flush()

# c0 = InputCell()
# c0.notebook = nb
# c0.input = 'import time'
# c0.output = ''
# nb.root = c0
# session.save(c0)
# session.flush()


    
    