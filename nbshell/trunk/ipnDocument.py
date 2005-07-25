import os

import wx
from lxml import etree

from notabene import notebook 

import IPythonLog
import Sheet

class FileSyntaxError(Exception):
    """Thrown in document.LoadFile when a syntax error ocurred while
    reading the file"""
    def __init__(self, f, lineno, msg = ""):
        """Initialization. "f" is the file object usually pointing
        near the position where the error ocurred. "lineno" is the line
        number of the file starting from 1. "msg" is an optional string
        explaining the error.
        """
        self.file = f
        self.line=lineno
        self.msg = msg

    def __str__(self):
        return "Error loading file: " + repr(f)+" at line: "+self.lineno+". "+msg
    
    
class ipnDocument(object):
    def __init__(self, app, notebookview):
        
        self.notebook = None # the notebook object
        self.logs = None # a dictionary of the logs
        self.sheet = None # The sheet object
        self.view = notebookview
        self.app = app
        self.factory = self.app.plugin_dict
        self.celllist = [] 
        self.fileinfo = { # contains various information of the file
                           # currently being edited
            "init":False, # This must be True when the
                           # structure is initialized
            "path":None,   # The path to the file
            "name":None,   # The name of the file.
            "script":None, # Is the file a script. If so here is the
                           # first line of the file to be copied when
                           # the file is saved
            "modified":False, # If true the file has been modified after the last save
            "untitled":False # This is set True by DefaultNotebook() and False by LoadFile()
            }
        self.DefaultNotebook() #Initialize notebook, logs, sheet

    def InsertCell(self, type, pos=-1, update = True, **kwds):
        """Inserts a cell of the given type with the given data at the given
        pos. If pos=-1 insert at the end. **kwds is passed to the
        plugin.Returns an instance to the cell"""
        factory = self.factory[type]
        cell = factory.CreateDocumentPlugin(self, **kwds)
        view = factory.CreateViewPlugin(cell, self.view)
        if pos == -1:
            self.addCell(cell)
        else:
            self.insertCell(cell, index)
        view.Update()
        if update : self.view.Update()
        return cell

    def DefaultNotebook(self):
        """Create a default empty notebook"""
        self.Clear()
        self.notebook = notebook.Notebook('untitled.nbk')
        self.logs = {'default-log':IPythonLog.IPythonLog(self, self.notebook, 'default-log')}
        etree.SubElement(self.notebook.root, 'sheet', format='rest')
        self.sheet = Sheet.Sheet(self, self.notebook)
        self.fileinfo['init'] = True
        self.fileinfo['path'] = os.getcwd()
        self.fileinfo['name'] = 'untitled.nbk'
        self.fileinfo['modified'] = False
        self.fileinfo['untitled'] = True
        
        log = self.logs['default-log']
        log.Append('\n\n')
        block = etree.XML("""
<ipython-block id="default-log">
    <ipython-input number="0"/>
</ipython-block>
""")
        self.sheet.element.append(block)
        self.InsertCell('python', ipython_block = block)
        self.view.Update()
        
    def Clear(self):
        """Clears the document. Does not ask for confirmation."""
        self.fileinfo["init"] = False
        for cell in self.celllist:
            cell.view.Close(update=False)
            self.delCell(cell.index)
        
        self.notebook = None
        self.logs = {}
        self.sheet = None
        
        

    def LoadFile(self, filename, overwrite = False):
        """Loads the file with the given filename. If there is currently a
        modified file in the document and overwrite is False, returns False
        and does nothing. If some error ocurred throws an exception. If
        everything is OK returns True. The UI should call this method"""

        #1. Is the previous document modified?
        if self.fileinfo["init"] and self.fileinfo["modified"] and not overwrite:
            return False
        self.Clear()
        
        #2. Create the notebook, log, sheet objects
        try:
            self.notebook = notebook.Notebook.from_file(filename)
            logids = self.notebook.root.xpath('//ipython-log/@id')
            self.logs = dict((x, IPythonLog.IPythonLog(self,self.notebook,x)) for x in logids)
            self.sheet = Sheet.Sheet(self, self.notebook)
            # Set up the fileinfo structure
            import os #dbg
            self.fileinfo["init"] = True
            self.fileinfo['path'], self.fileinfo["name"] = os.path.split(filename)
            if self.fileinfo['path'] == '':
                self.fileinfo['path'] = os.getcwd()
            self.fileinfo["modified"] = False
            self.fileinfo['untitled'] = False
            
        except:
            self.Clear()
            raise
        
        #3. Create the plugins that display the content. TODO: This should not be here
        if self.sheet.element.text is not None:
            self.InsertCell('plaintext',update=False,element = self.sheet.element)
        for elem in self.sheet.element:
            self.InsertCell('python', update=False, ipython_block = elem)
            if elem.tail is None:
                elem.tail = ''
            self.InsertCell('plaintext', update=False, element = elem)
        self.view.Update()
        return True
    
    def IsModified(self):
        """returns if the file has been modified since last save"""
        #TODO: Right now there is no point in doing anything useful
        #here. When things are done fix it
        return True
        

    def SaveFile(self, filename = None):
        """Saves the file. If filename is given use this as a file name and
        change self.fileinfo['name']. If filename is None use
        self.fileinfo['name']. If the file is saved successfully return True.
        If there are problems opening the file throws an exception. """

        if filename is None:
            print 'fileinfo -> %s'%str(self.fileinfo) #dbg
            if (not self.fileinfo['init']) or self.fileinfo['name'] is None:
                raise Exception
            else:
                filename = self.fileinfo['path'] + self.fileinfo['name']
        mod = self.fileinfo['modified']
        try:
            #1. update the data from the views
            for doccell in self.celllist:
                doccell.view.UpdateDoc()
            print 'root-> %s'%str(self.notebook.root)
            etree.dump(self.notebook.root)
            self.notebook.write(filename)
        except:
            self.fileinfo['modified'] = mod
            raise
        self.fileinfo['path'], self.fileinfo['name'] = os.path.split(filename)
        if self.fileinfo['path'] == '':
            self.fileinfo['path'] = os.getcwd()
        self.fileinfo['modified'] = False
        

    def addCell(self, cell):
        self.celllist.append(cell)
        cell.index = len(self.celllist) - 1
        

    def delCell(self, index):
        del(self.celllist[index])
        def f(x):
            self.celllist[x].index = x
            return None
        map(f, range(index, len(self.celllist))) # fix the indeces of the cells
#        self.view.delCell(index) # delete the window at the end,
                                 # because the windows might need to
                                 # know their new indeces while relaying out

    def insertCell(self, cell, index):
        cell.index = index
        self.celllist.insert(cell, index)
        def f(x):
            self.cellist[x].index = x
            return None
        map(f, range(index, len(self.celllist))) # fix the indeces of the cells
        #self.view.insertCell(cell.GetWindow()) # see the comment at delCell
    
    def GetCell(self, index):
        return self.celllist[index]

