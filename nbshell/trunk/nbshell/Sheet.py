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

from notabene import notebook

from nbshell import PythonPlugin
from nbshell.utils import getindex


class Sheet(object):
    def __init__(self, doc, notebook, view, factory):
        self.doc = doc
        self.notebook = notebook
        self.element = self.notebook.root.xpath('//sheet')[0]
        self.view = view
        self.factory = factory
        self.celllist = []
        self.last = False
        # cell2sheet stores all elements in a sheet corresponding to a given
        # element in a given cell in a log. It is a dictionary with keys of
        # the type (log, cellnumber, type), where 'log' is the name of the
        # log, cellnumber is an integer, and type is one of 'input',
        # 'special', 'output', etc. The values of the dictionary are lists of
        # tuples of the type (block, id) where block is a PythonDocumentPlugin
        # object and the corresponding element is block.block[id]
        self.cell2sheet = {}
        # sheet2sheet is a dictionary. For each element in a block it returns
        # the list in cell2sheet in which this element belongs and the index
        # in it The key is of type (index,id) where index is block.index and
        # id has the same meaning as in cell2sheet. The value is a tuple
        # (list, index)
        self.sheet2sheet = {}
        
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
            print 'cell-> %s, pos->%s'%(str(cell),str(pos))
            self.__insert_cell(cell, pos)
        if update:
            view.Update()
            self.view.Update()
        return cell

    def Update(self, update = True, celllist = False, dicts = False, output = False):
        
        """Updates the sheet. If update is True calls the Update method for
        each cell in celllist. 

        If celllist is True recreates the cells in celllist. Call this with
        celllist = True if the structure of the sheet was changed outside the
        Sheet class. 

        If dicts is True updates self.cell2sheet and self.sheet2sheet. Use
        this if some of the ipython-block elements was changed outside of the
        Sheet class. In order for Update(dicts=True) to work properly,
        celllist must be updated. 

        If output is True calls UpdateOutput for each cell in the logs. Use
        this when you rerun parts of the log to add all the new outputs to the
        sheet and delete the ones which don't exist after the rerun.
        """
        
        if celllist:
            #TODO: Here I clear the celllist and then recreate it. This is
            #slow and causes flicker. What I should do is check every cell if
            #it corresponds to the contents in self.element and if not change
            #it.

            self.__clear_celllist(update = False)
            self.__update_celllist(update = False)
        if dicts:
            self.__update_dicts()
        if output:
            logs = self.doc.logs
            for logid in logs.keys():
                for cell in (notebook.Cell(x) for x in logs[logid].log):
                    self.UpdateOutput(logid, cell, update = False)
        if update:
            for cell in self.celllist:
                cell.view.Update()
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
        self.celllist.insert(index, cell)
        def f(x):
            self.celllist[x].index = x
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
        """Adds an empty input element at the last block of each log"""
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
                self.InsertElement(cell,'input',lastcell, update = update)
                passedlogs.update({logid:True})
        #if update:
        #    self.view.Update()
            
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
                self.DeleteElement(cell, -1,update)
                passedlogs.update({logid:True})
        #if update:
        #    self.view.Update()

    def __update_dicts(self):
        """Update self.cell2sheet and self.sheet2sheet, provided that for each
        <ipython-block> we have created the corresponding PythonDocumentPlugin
        object"""
        
        self.cell2sheet = {}
        self.sheet2sheet = {}
        for block in self.celllist:
            # check if block is a PythonDocumentPlugin object
            try:
                logid = block.logid
            except:
                continue
            for (i, cell) in enumerate(block.cells):
                key = (logid, cell.number, block.block[i].attrib['type'])
                val = self.cell2sheet.get(key,[])
                val.append((block, i))
                self.cell2sheet[key] = val
                val2 = (val, len(val)-1)
                self.sheet2sheet[(block.index,i)] = val2

    def DefaultSheet(self , update = True):
        """Create a default sheet"""
        self.Clear(update = False)
        #Create a default sheet
        #Here we don't need to call SetLastInputs, because
        #default_sheet will append the last input in the log here
        #We only need to set self.last
        self.element = self.notebook.default_sheet()
        self.element.text = \
""" This is a temporary message, until I write proper help. Please use Return
to insert new lines and Shift-Return to execute inputs.
"""
        
        # Now remove the old sheet and replace it with the new one
        oldsheet = self.notebook.root.find('sheet')
        if oldsheet is not None:
            self.notebook.root.remove(oldsheet)
        self.notebook.root.append(self.element)
        self.last = True
        #etree.dump(self.element) #dbg
        #etree.dump(self.notebook.root) #dbg
        #Here we do not call InsertElement, so we must update the dictionaries
        self.Update(update, celllist = True, dicts = True)
        
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
            
    def InsertElement(self, block, type, cell, pos = None, update = True):
        """Inserts an element of type <ipython-cell> in a ipython block. block
        is an object of type PythonDocumentPlugin. pos is the position at
        which the element will be inserted. Negative positions are also
        accepted. pos=None will append the element at the end of the block.
        type is the tvalue of the 'type' attribute of the element and cell is
        a Cell object from the log. If update is true update the block"""
        
        #1. Add the element
        l = len(block.block)
        if pos is None:
            pos = l
        elif pos < 0:
            pos = l + pos
        number = cell.number

        element = etree.Element('ipython-cell',type = type, number = str(number))
        block.block[pos:pos] = [element]
        block.cells[pos:pos] = [cell]
        
        if update:
            block.view.Update()
            
        l +=1

        
        #2. Update self.cell2sheet and self.sheet2sheet
        #2.1 Update the dicts for element
        key = (block.logid,number,type)
        value = self.cell2sheet.get(key, [])
        value.append((block,pos))
        self.cell2sheet.update({key:value})
        #2.2 Update the dicts for the elements after the one we inserted
        #Incremenet the posiotion in the block for each element, and change
        #sheet2sheet keys correspondingly
        for p in reversed(range(pos+1,l)):
            val = self.sheet2sheet[(block.index,p-1)] 
            val[0][val[1]] = (block, p)
            del self.sheet2sheet[(block.index,p-1)]
            self.sheet2sheet[(block.index,p)] = val
        #update sheet2sheet info for the inserted element
        self.sheet2sheet.update({(block.index,pos):(value,len(value)-1)})
    
    def DeleteElement(self, block, pos, update = True):
        """Deletes the element <ipython-cell> which is at position pos in the
        given block. block is an object of class PythonDocumentPlugin. pos can
        be negative"""
        
        #1. Delete the element
        l = len(block.block)
        if pos < 0:
            pos = l + pos
        elem = block.block[pos]
        del(block.block[pos])
        del(block.cells[pos])
        if update:
            block.view.Update()
        
        #2. Update cell2sheet and sheet2sheet
        #2.1 Update the dicts for the element
        key = (block.logid,int(elem.attrib['number']),elem.attrib['type'])
        val = self.sheet2sheet[(block.index,pos)]
        del val[0][val[1]]
        if len(val) == 0:
            del self.cell2sheet[key]
        del self.sheet2sheet[(block.index,pos)]
        #2.2 Update the dicts for the other elements
        #2.2.1 change sheet2sheet values for all elements in val[0] with index >=val[1]
        for (blk, pos) in val[0][val[1]:]:
            self.sheet2sheet[(blk.index,pos)][1] -= 1
        #2.2.2 update the keys in sheet2sheet and values in cell2sheet for all
        #elements after the one we deleted
        for p in range(pos,l-1):
            val = self.sheet2sheet[(block.index,p+1)] 
            val[0][val[1]] = (block, p)
            del self.sheet2sheet[(block.index,p+1)]
            self.sheet2sheet[(block.index,p)] = val

    def __update_list(self, clist):
        """Updates the view of the given list of cells. It is possible that
        one object is in more than one place in the list. In that case we
        update it only once"""
        oldindex = -1
        for cell in sorted(clist, key = lambda x:x.index):
            index = cell.index
            if index > oldindex:
                cell.view.Update()
                oldindex = index

    def __update_type (self, block, cell, pos2add, type, update = False):
        """ Updates the output element of type 'type' corresponding to the
        given input element. pos2add is the position at which to insert a new
        element in 'block' if needed. Returns a tuple (pos2add, blocklist)
        where pos2add is the updated insert position and blocklist is a list
        of blocks which have been modified"""

        logid = block.logid
        number = cell.number
        blocklist = []
        #1. Are there stderr elements corresponding to the given input in the cell?
        oldelems = self.cell2sheet.get((logid,number,type),[])
        if len(oldelems) > 0:
            #1.1 There are such elements
            
            #Has the input produced output of given type?
            if cell.element.find(type) is not None:
                #1.1.1 Yes. Check if one of the elements is on the insert
                #position.
                if len(block.block)>pos2add and \
                   block.cells[pos2add] == cell and \
                   block.block[pos2add].attrib['type'] == type :
                    #Increment the insert position
                    pos2add += 1
                #Else do nothing
            else:
                #1.1.2 No. Delete all output cells of given type in the sheet
                [self.DeleteElement(block, pos, update = False) \
                 for (block,pos) in oldelems]
            
            blocklist = (x[0] for x in oldelems)
            if update:
                self.__update_list(self, blocklist)
        else:
            #1.2 There are no such elements
            
            #Has the input produced given output?
            if cell.element.find(type) is not None:
                #1.2.1 Yes. Insert the element at the insert position and
                #increment it
                self.InsertElement(block,type,cell,pos2add,update = False)
                pos2add += 1
                if update:
                    block.view.Update()
                blocklist = [block]
            #else:
                #1.2.2 No. Do nothing
        return (pos2add, blocklist)
    
    def UpdateOutput(self, logid, cell, update = True):
        """Updates the output elements of the sheet corresponding to the given cell
        element."""

        # Get all the <ipython-cell type='special'> or <ipython-cell type='input'>
        # that correspond to the cell (usually there is only one)
        inputelems = self.cell2sheet.get((logid, cell.number, 'special'),[])
        if inputelems == []:
            inputelems = self.cell2sheet.get((logid, cell.number, 'input'),[])
        
        #for each input update the outputs calling __update_type. TODO:There
        #are some problems here if there are two or more input elements in the
        #sheet coresponding to one cell.

         
        blocklist = []

        #I cange the contents of the list here, so I use indexes
        for i in range(len(inputelems)):
            #pos2add is the position at which a new element will be inserted in
            #the log
            pos = inputelems[i][1]
            block = inputelems[i][0]
            pos2add = pos + 1
            cell = block.cells[pos]
            # TODO: Handle traceback
            for type in ['stderr', 'stdout', 'output']:
                pos2add, list = self.__update_type(block, cell, pos2add, type,\
                                           False)
                blocklist.extend(list)

        if update:
            self.__update_list(blocklist)

    def ReplaceCells(self, logid, oldcell, newcell, update = True):
        """Changes all the <ipython-cell type=..., number=oldcell.number> elements to
        elements with number=newcell.number. """
        
        #TODO: The algorithm here could be faster.
        
        types = ['input', 'special', 'stdout', 'stderr', 'output','traceback']
        for type in types:
            val = self.cell2sheet.get((logid, oldcell.number, type),[])
            for (block,pos) in val:
                block.block[pos].attrib['number'] = str(newcell.number)
                block.cells[pos] = newcell
        self.Update(update, dicts = True)

    def InsertText(self, block, pos, update = True):
        """Splits the given block and inserts a text cell"""
        index = getindex(self.element,block.block)
        #Get the XML for the new ipython-block
        nextblock = block.Split(pos)
        #update the old text cell to point to the new block
        oldtextcell = self.celllist[block.index+1]
        nextblock.tail = oldtextcell.GetText()
        oldtextcell.element = nextblock
        #insert nextblock in the sheet
        self.element[index+1:index+1] = [nextblock]
        ind = oldtextcell.index
        self.InsertCell('python',ind, update = False, \
                        ipython_block = nextblock)
        #insert a new text cell in the celllist
        self.InsertCell('plaintext', ind, update = False, element = block.block)
        #update
        self.Update(dicts = True)
        if update:
            self.__update_list(self.celllist[ind-1:ind+2])
            self.view.Update()