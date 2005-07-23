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

            "name":None,   # The name of the file. If None, it should be
                           # assigned at first save

            "script":None, # Is the file a script. If so here is the
                           # first line of the file to be copied when
                           # the file is saved
            "modified":False # If true the file has been modified after the last save
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
        self.fileinfo['name'] = 'untitled.nbk'
        self.fileinfo['modified'] = False
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
        
    def _loadFile(self, f):
        """Clears the document then loads the given file. Does not ask
        for confirmation yet. "f" is a file object, not a filename. If error occurs throws FileSyntaxError"""
        self.Clear()
        #1. Confirm this is a ipn file
        lineno = 0
        line = f.readline()
        lineno +=1
        
        if line[0:5] != "#@ipn":
            if line[0:2] != "#!":
                raise FileSyntaxError(f,lineno,"File is not ipn file")
            else:
                line = f.readline()
                self.fileinfo["script"] = line
                lineno += 1
                if line[0:5] != "#@ipn":
                    raise FileSyntaxError(f, lineno, "File is not ipn file")
        
        #2. Start reading lines
        for line in f:
            lineno +=1

            if line.isspace():
                continue
            line = line.lstrip()
            #Read commands. So far the only commands are #@# and #@cell
            if line[0:3] == "#@#":
                continue
            elif line[0:7] == "#@cell ":
                #Start processing the cell
                args = line[7:].lstrip().split()
                cell = self.InsertCell(args[0], update=False)
                t = self.app.plugin_dict[args[0]].type
                if t == "raw": #pass raw data to the cell
                    cnt = cell.LoadRaw(f, args)
                    lineno += cnt
                elif t == "encoded": #pass encoded data
                    def gener(param): #hack to be able to return the line count
                        param[0] = 0
                        for l in f:
                            param[0]+=1
                            l = l.lstrip()
                            if l[0:9] == "#@endcell":
                                break
                            elif l[0:3] == "#% ":
                                yield l[3:]
                            elif l[0:3] == "#@#":
                                continue
                            else:
                                raise FileSyntaxError(f,lineno,"Wrong syntax")
                    p = [0,0]
                    cell.LoadEncoded(gener(p), args)
                    lineno+=p[0]
                
        self.view.Update()

    def LoadFile(self, filename, overwrite = False):
        """Loads the file with the given filename. Internally uses
        _loadFile, however, this is a more userfriendly version and
        also sets the fileinfo structure. Does not check the system
        path. If there is currently a modified file in the document
        and overwrite is False, returns False and does nothing. If
        some error ocurred throws the corresponding exception. If
        everything is OK returns True. The UI should call this method"""

        if self.fileinfo["init"] and self.fileinfo["modified"] and not overwrite:
            return False
        self.Clear()
        try:
            # Set up the fileinfo structure
            self.fileinfo["init"] = True
            self.fileinfo["name"] = filename
            f = file(filename, "r")
            self._loadFile(f)
            f.close()
        except:
            self.Clear()
            raise
        return True
    
    def IsModified(self):
        """returns if the file has been modified since last save"""
        #TODO: Right now there is no point in doing anything useful
        #here. When things are done fix it
        return True
        
    def _saveFile(self, f):
        """Saves data to the file object f"""
        if self.fileinfo["init"] and (self.fileinfo["script"] is not None):
            f.write(self.fileinfo["script"])
        f.write("#@ipn\n")
        for cell in self.celllist:
            factory = cell.GetFactory()
            celltype = factory.type
            args = " ".join(cell.GetArgs()) #TODO: check if the argumens don't use bad symbols as EOL for example
            f.write("#@cell "+args + "\n") 
            if celltype == "raw":
                cell.Serialize(file = f)
            else:
                def encode(f,x):
                    f.write("#% "+x) #The newline is written by cell.Serialize
                cell.Serialize(encodefunc = lambda x:encode(f,x)) 
            f.write("#@endcell\n")
        self.fileinfo["modified"] = False
            

    def SaveFile(self, filename = None):
        """Saves the file. If filename is given use this as a file
name and change self.fileinfo['name']. If filename is None use
self.fileinfo['name']. If self.fileinfo is not initialized return
False. If the file is saved successfully return True. If there are
problems opening the file throws an exception.
"""
        if filename is None:
            if (not self.fileinfo["init"]) or self.fileinfo["name"] is None:
                return False
            else:
                filename = self.fileinfo["name"]
        mod = self.fileinfo["modified"]
        try:
            f = file(filename,"w")
            self._saveFile(f)
            f.close()
        except:
            self.fileinfo["modified"] = mod
            raise
        self.fileinfo["name"] = filename
            
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

