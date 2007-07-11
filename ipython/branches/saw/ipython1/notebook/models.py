import datetime
from sqlalchemy import *

db = create_engine('sqlite:///notebook.db')

metadata = BoundMetaData(db)

metadata.engine.echo = True

# Tables

nodes_table = Table('nodes', metadata,
    Column('node_id', Integer, primary_key=True),
    Column('parent_id', Integer, ForeignKey('nodes.node_id')),
)

cells_table = Table('cells', metadata,
    Column('cell_id', Integer, primary_key=True),
    Column('created', DateTime),
    Column('modified', DateTime),
    Column('node_id', Integer, ForeignKey('nodes.node_id')),
    Column('sequence_number', Integer)    
    )

input_cells_table = Table('input_cells', metadata,
    Column('cell_id', Integer, ForeignKey('cells.cell_id'), unique=True),
    Column('input', String()),
    Column('output', String()) 
)

text_cells_table = Table('text_cells', metadata,
    Column('cell_id', Integer, ForeignKey('cells.cell_id'), unique=True),
    Column('text_data', String()),
)

notebooks_table = Table('notebooks', metadata,
    Column('notebook_id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('users.user_id')),
    Column('created', DateTime),
    Column('modified', DateTime),
    Column('root_id', Integer, ForeignKey('nodes.node_id')),    
)
    
users_table = Table('users', metadata,
    Column('user_id', Integer, primary_key=True),
    Column('username', String(40)),
    Column('email', String(40)),
    Column('created', DateTime),
    Column('modified', DateTime)
)

def createTables():
    nodes_table.create()
    cells_table.create()
    notebooks_table.create()
    users_table.create()
    input_cells_table.create()
    text_cells_table.create()
    

# Mappers

class Node(object):
    pass

class Created(object):
    def __init__(self):
        self.created = datetime.datetime.now()

class Modified(object):
    def setModified(self):
        self.modified = datetime.datetime.now()

class Timestamper(Created, Modified):
    def __init__(self):
        super(Timestamper, self).__init__()

class Cell(Timestamper):
    pass

class InputCell(Cell):
    pass
    # def __init__(self,input='',output=''):
    #     super(Cell, self).__init__()
    #     self.input = input
    #     self.output = output

    # def __repr__(self):
    #     s = """Cell ID: %d
    #     Input: %s
    #     Output: %s
    #     Created: %s""" 
    #     return s % (self.cell_id, 
    #                 self.input, 
    #                 self.output,
    #                 self.created.ctime())

class TextCell(Cell):
    pass

class User(Timestamper):
    pass
    # def __init__(self, name='', email=''):
    #     super(User, self).__init__()
    #     self.username = name
    #     self.email = email
    #     
    # def __repr__(self):
    #     s = """User ID: %d
    #     Username: %s
    #     Email: %s
    #     Created: %s"""
    #     return s % (self.user_id,
    #                 self.username, 
    #                 self.email,
    #                 self.created.ctime())

class Notebook(Timestamper):
    pass
    # def __repr__(self):
    #     super(Notebook, self).__init__()
    #     s = """Notebook ID: %d
    #     User ID: %d
    #     Created: %s""" 
    #     return s % (self.notebook_id,
    #                 self.user_id,
    #                 self.created)

def createMappers():
    nodemapper = mapper(Node, nodes_table,
        properties=dict(inputCells=relation(InputCell, 
                            cascade="all, delete-orphan"),
                        textCells=relation(TextCell, 
                            cascade="all, delete-orphan"),
                        children=relation(Node, 
                            cascade="all, delete-orphan", backref='parent')))
    cellmapper = mapper(Cell, cells_table)
    inputcellmapper = mapper(InputCell, input_cells_table, inherits=cellmapper)
    textcellmapper = mapper(TextCell, text_cells_table, inherits=cellmapper)
    usermapper = mapper(User, users_table,
        properties=dict(notebooks=relation(Notebook, 
            cascade="all, delete-orphan", backref='user')))
    notebookmapper = mapper(Notebook, notebooks_table, 
        properties=dict(root=relation(Node, uselist=False)))
    
    # usermapper.add_property('notebooks', relation(Notebook))

    
# Initialization

createTables()
createMappers()

# Actually do some transactions

session = create_session()

# bgranger = User()
# bgranger.username = 'bgranger'
# bgranger.email = 'ellisonbg@gmail.com'
# session.save(bgranger)
# 
# nb0 = Notebook()
# nb0.user_id

#c = Cell()
#c.input = 'foo'
#c.output = 'bar'

#session.save(c)

#session.flush()


    
    