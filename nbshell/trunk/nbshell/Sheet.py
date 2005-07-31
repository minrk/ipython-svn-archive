"""Class Sheet. Responsible for storing and manipulating data in the <sheet> tag"""

#*****************************************************************************
#       Copyright (C) 2005 Tzanko Matev. <tsanko@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from nbshell import Release
__author__  = '%s <%s>' % Release.author
__license__ = Release.license
__version__ = Release.version


from lxml import etree

from nbshell import PythonPlugin


class Sheet(object):
    def __init__(self, doc, notebook, view, factory):
        self.doc = doc
        self.notebook = notebook
        self.element = self.notebook.root.xpath('//sheet')[0]
        self.view = view
        self.factory = factory
        self.celllist = []
        self.last = False
        
    def InsertCell(self, type, pos=-1, update = True, **kwds):
        """Inserts a cell of the given type with the given data at the given
        pos. If pos=-1 insert at the end. **kwds is passed to the
        plugin.Returns an instance to the cell"""
        factory = self.factory[type]
        cell = factory.CreateDocumentPlugin(self.doc, **kwds)
        view = factory.CreateViewPlugin(cell, self.view)
        if pos == -1:
            self.__add_cell(cell)
        else:
            self.__insert_cell(cell, index)
        view.Update()
        if update : self.view.Update()
        return cell

    def Update(self, update = True, celllist = True):
        
        """Updates the sheet. If celllist is true recreates all cells from
        data in self.element. If update is false does not update the Notebook
        widget view. You should call this method whenever the contents of the
        <sheet> element has been changed outside the Sheet class (like for
        example in ipnDocument.LoadFile()). Use celllist = True only when the
        structure of the sheet has changed """
        
        if celllist:
            #TODO: Here I clear the celllist and then recreate it. This is
            #slow and causes flicker. What I should do is check every cell if
            #it corresponds to the contents in self.element and if not change
            #it.

            self.__clear_celllist(update = update)
            self.__update_celllist(update)
        else:
            for cell in self.celllist:
                cell.view.Update()
            if update:
                self.view.Update()
    
    def UpdateDoc(self):
        """Updates data from the view"""
        for doccell in self.celllist:
            doccell.view.UpdateDoc()

    def __update_celllist(self, update = False):
        """Updates the celllist from self.element and updates the view if
        update == True """
        if self.element.text is not None:
            self.InsertCell('plaintext',update=False,element = self.element)
        for elem in self.element:
            self.InsertCell('python', update=False, ipython_block = elem)
            if elem.tail is None:
                elem.tail = ''
            self.InsertCell('plaintext', update=False, element = elem)
        if update:
            self.view.Update()
        
    def __clear_celllist(self, update = False):
        """Clears the celllist. if update = True, updates the view"""

        #since I modify celllist, I cannot use a statement like:
        #   for cell in celllist
        l = len(self.celllist)
        for i in range(l):
            cell = self.celllist[-1]
            cell.view.Close(update=False)
            self.__del_cell(cell.index)
        if update:
            self.view.Update()

    def __add_cell(self, cell):
        self.celllist.append(cell)
        cell.index = len(self.celllist) - 1
        

    def __del_cell(self, index):
        del(self.celllist[index])
        def f(x):
            self.celllist[x].index = x
            return None
        map(f, range(index, len(self.celllist))) # fix the indeces of the cells
        #self.view.delCell(index) # delete the window at the end,
                                 # because the windows might need to
                                 # know their new indeces while relaying out

    def __insert_cell(self, cell, index):
        cell.index = index
        self.celllist.insert(cell, index)
        def f(x):
            self.cellist[x].index = x
            return None
        map(f, range(index, len(self.celllist))) # fix the indeces of the cells
        #self.view.insertCell(cell.GetWindow()) # see the comment at delCell
    
    def GetCell(self, index):
        return self.celllist[index]

    def Clear(self, update = True):
        """Clears the sheet"""
        self.element.text = None
        self.element.clear()
        self.__clear_celllist()
        if update:
            self.view.Update()


    def SetLastInputs(self, update = True):
        """Adds an empty input element at the last blog of each log"""
        if self.last:
            return
        self.last = True
        passedlogs = {}
        for cell in reversed(self.celllist):
            try:
                log = cell.log #Check if cell is a python plugin
            except:
                continue
            logid = cell.logid
            if logid not in passedlogs: #then this is the last block for that log
                lastcell = log.lastcell
                element = etree.Element('ipython-input', number =
                                        str(lastcell.number))
                #TODO: This is spagetti code
                cell.block.append(element)
                cell.cells.append(lastcell)
                
                cell.view.Update()
                passedlogs.update({logid:True})
        if update:
            self.view.Update()
            
    def ClearLastInputs(self, update = True):
        """Clears the last inputs of each log. This should be called before
        the file is saved"""
        if not self.last:
            return
        self.last = False
        passedlogs = {}
        for cell in reversed(self.celllist):
            try:
                log = cell.log #Check if cell is a python plugin
            except:
                continue
            logid = cell.logid
            if logid not in passedlogs: #then this is the last block for that log
                #TODO: spagetti
                del(cell.block[-1])
                del(cell.cells[-1])
                cell.view.Update()
                passedlogs.update({logid:True})
        if update:
            self.view.Update()

    def DefaultSheet(self , update = True):
        """Create a default sheet"""
        self.Clear()
        #Create a default sheet
        #Here we don't need to call SetLastInputs, because
        #default_sheet will append the last input in the log here
        #We only need to set self.last
        self.element = self.notebook.default_sheet()
        self.last = True
        # Now remove the old sheet and replace it with the new one
        oldsheet = self.notebook.root.find('sheet')
        if oldsheet is not None:
            self.notebook.root.remove(oldsheet)
        self.notebook.root.append(self.element)
        #etree.dump(self.element) #dbg
        etree.dump(self.notebook.root) #dbg
        self.Update(update)
        
    def IsModified(self):
        """returns if the sheet has been modified since last save"""
        for cell in self.celllist:
            if cell.modified:
                return True
        return False
    modified = property(fget = IsModified)
    
    def SetSavePoint(self):
        """ Sets the save point of the document. It is used to determine if
        the document was modified after the last save"""
        for cell in self.celllist:
            cell.SetSavePoint()
