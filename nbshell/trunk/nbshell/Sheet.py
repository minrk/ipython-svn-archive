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
        #self.last stores if last input has been set. Used by SetLastInput,ClearLastInput
        self.last = None
        #self.currentlog stores the current log. It will be possible to change
        #it in the future
        self.currentlog = 'default-log'
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

        #self.__currentcell stores the current cell. It is retrieved by the 
        #self.currentcell property
        self._currentcell = None
        
    def __get_current_cell(self):
        return self._currentcell
    def __set_current_cell(self, cell):
        self._currentcell = cell
        cell.view.SetFocus()
    currentcell = property(fget = __get_current_cell, fset = __set_current_cell)
    
    def InsertCell(self, type, pos=-1, update = True, **kwds):
        """Inserts a cell of the given type with the given data at the given
        pos. If pos=-1 insert at the end. **kwds is passed to the
        plugin.Returns an instance to the cell"""
        #TODO: Update the dicts here
        factory = self.factory[type]
        cell = factory.CreateDocumentPlugin(self.doc, **kwds)
        view = factory.CreateViewPlugin(cell, self.view)
        if pos == -1:
            self.__add_cell(cell)
        else:
            print 'cell-> %s, pos->%s'%(str(cell),str(pos)) #dbg
            self.__insert_cell(cell, pos)
        if update:
            view.Update()
            self.view.Update()
        return cell
    
    def DeleteCell(self, cell, update = True):
        """Deletes a given element in celllist"""
        if cell in [self.celllist[-1], self.celllist[0]]:
            #This is the first or the last text cell and cannot be deleted.
            #Just clear the text.
            cell.SetText('')
            if update:
                cell.view.Update()
            return
        
        try:
            cell.log
        except:
            #This is a text cell
            self.__del_text_cell(cell, update)
        else:
            #This is a python cell
            self.__del_code_cell(cell,update)

    def __del_text_cell(self,cell,update = False):
        """Deletes the given text cell. Does not check if this is the first or
        last text cell"""
        #TODO: write this
        return
        
    def __del_code_cell(self,cell,update = False):
        #TODO: write this
        return

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
        l = len(self.element)
        for i in range(l):
            elem = self.element[i]
            if elem.tag == 'ipython-block':
                self.InsertCell('python', update=False, ipython_block = elem)
            elif elem.tag == 'ipython-figure':
                self.InsertCell('figure', update = False, element = elem)
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
        self.last = None
        if update:
            self.view.Update()

    #The last cell for input of each log is not a part of the notebook. It is
    #added after the notebook has loaded and is used to add append cells to
    #the logs. Since it should not be a part of the notebook file I have two
    #methods SetLastInputs and ClearLastInputs to handle the last cell.
    def SetLastInputs(self, update = True):
        """Adds an empty input element at the last block of each log or
        restores the last inputs from the previous ClearLastInputs. You should
        not modify the sheet between the calls of SetLastInputs and
        ClearLastInputs"""
        if self.last is None: #We have not called ClearLastInputs before
            self.last = True
            passedlogs = {}
            blocklist = []
            for block in reversed(self.celllist):
                try:
                    log = block.log #Check if cell is a python plugin
                except:
                    continue
                logid = block.logid
                if logid not in passedlogs: #then this is the last block for that log
                    lastcell = log.lastcell
                    self.InsertElement(block,'input',lastcell, update = False)
                    blocklist.append(block)
                    passedlogs.update({logid:True})
            if update:
                self.__update_list(blocklist)
                self.view.Update()
        elif not self.last: #We have called ClearLastInputs
            #Restore the last inputs
            self.last = True
            blocklist = []
            l = len(self.undostack)
            for i in range(l):
                (key,value) = self.undostack.pop()
                log = self.doc.logs[key[0]]
                cell = log.lastcell
                self.InsertElement(value[0],key[2],cell,value[1],update = False)
                blocklist.append(value[0])
            if update:
                self.__update_list(blocklist)
                self.view.Update()

    def ClearLastInputs(self, update = True):
        """Clears the last inputs of each log. This should be called before
        the file is saved"""
        if not self.last:
            return
        self.last = False
        self.undostack = []
        for logid in self.doc.logs.keys():
            log = self.doc.logs[logid]
            lastcell = log.lastcell
            #The last cells should only have inputs
            key = (logid, lastcell.number, 'input')
            inputs = self.cell2sheet[key]
            while inputs != []:
                input = inputs[0]
                self.undostack.append((key,input))
                self.DeleteElement(inputs[0][0],inputs[0][1])

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
        #1. Are there elements corresponding to the given input in the cell?
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
    
    def __update_figures(self, figurelist, block, pos2add, update = False):
        """Updates the figures which where created by running the cell. The
        figures will be appended at pos2add and the block will be split in two
        if necessary. Returns a tuple (numfig, blocklist) where numfig is the
        number of figures inserted and blocklist is the same as in
        __update_type"""
        blocklist = []
        numfig = 0
        for figurexml in reversed(figurelist):
            self.InsertFigure(block, pos2add,figurexml, update = False)
            numfig +=1
        if numfig>0:
            #TODO: smarter update of blocks?
            blocklist = self.celllist
        return (numfig, blocklist)
        
    def UpdateOutput(self, logid, cell, update = True, block=None, pos = None):
        """Updates the output elements of the sheet corresponding to the given
        cell element. If block and pos are given they are regarded as the
        <ipython-cell> element which was called to run the cell. They are used
        to place any produced figures at a meaningful place. If block and pos
        are not given the figures will be placed after the last input
        <ipython-cell> element in the document corresponding to the given cell.
        
        The return value is None if no new code blocks were created or a new
        code block. The new block must be used for appending the new input
        element """

        cell.update()
        # Get all the <ipython-cell type='special'> or <ipython-cell type='input'>
        # that correspond to the cell (usually there is only one)
        inputelems = self.cell2sheet.get((logid, cell.number, 'special'),[])
        if inputelems == []:
            inputelems = self.cell2sheet.get((logid, cell.number, 'input'),[])
        if inputelems == []:
            #There are no inputs in the sheet corresponding to the given cell
            return None
        
        #for each input update the outputs calling __update_type. TODO:There
        #are some problems here if there are two or more input elements in the
        #sheet coresponding to one cell.

         
        blocklist = []
        #Sort inputelems so that we may deal with the one after which
        #to add the figures last
        inputelems = sorted(inputelems, cmp = lambda x,y:\
                            cmp((x[0].index,x[1]),(y[0].index,y[1])))
        if block != None:
            #A current block and position were given
            index = 0
            while inputelems[index][0] != block and inputelems[index][1] != pos:
                index+=1
            if index <= len(inputelems):
                #A matching element was found. Swap it with the last element
                inputelems[-1], inputelems[index] = inputelems[index],\
                inputelems[-1]

        #I change the contents of the list here, so I use indexes
        #We deal with the last element separately
        for i in range(len(inputelems)-1):
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
        #Deal with the last element
        #pos2add is the position at which a new element will be inserted in
        #the log
        pos = inputelems[-1][1]
        block = inputelems[-1][0]
        pos2add = pos + 1
        cell = block.cells[pos]
        # TODO: Handle traceback
        # Handle stderr
        pos2add, list = self.__update_type(block, cell, pos2add, 'stderr',\
                                           False)
        blocklist.extend(list)
        #Handle figures. We use flag to determine if we need to insert a new
        #block after the figures
        if pos2add >= len(block):
            flag = True
        else:
            flag = False
        figuredict = getattr(self.doc.logs[logid], 'figuredict', None)
        if figuredict is not None:
            figurelist = figuredict.get(cell.number, None)
            if figurelist is not None:
                numfig, list = self.__update_figures(figurelist, block, pos2add,\
                                                     update = False)
                del(figuredict[cell.number])
            else:
                numfig,list = 0,[]
        else:
            numfig,list=0,[]
        blocklist.extend(list)
        retvalue = None
        if numfig > 0:
            #We have added figures. Determine where the other output will go
            if not flag:
                #The figures were inserted inside a block. Get the rest
                #of the block
                block = self.celllist[block.index+numfig+1]
                pos2add = 0
            else:
                #Insert a new code block after the figures
                index = block.index + numfig
                lastfig = self.celllist[index]
                codeelem = etree.Element('ipython-block', logid = block.logid)
                #Fix the text
                if index < len(self.celllist)-1 and\
                   self.celllist[index+1].type == 'plaintext':
                    textblock = self.celllist[index+1]
                    codeelem.tail = textblock.GetText()
                    textblock.element = codeelem
                    blocklist.append(textblock)
                #Insert the new block
                block = self.InsertCell('python', index+1, update = False,\
                                        ipython_block = codeelem)
                self.Update(update = False, dicts = True)
                retvalue = block
                blocklist.append(block)
                pos2add = 0
        #Deal with other output
        for type in ['stdout', 'output']:
            pos2add, list = self.__update_type(block, cell, pos2add, type,\
                                               False)
            blocklist.extend(list)
            
        if update:
            self.Update(update = True)
        return retvalue
#            self.__update_list(blocklist)


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
            
    def InsertCode(self, block, pos, update = True):
        """Splits the given text block and inserts a code block. The logid
        for the new block is set in self.currentlog"""
        assert(self.last) #The last inputs must be set
        newtext = block.Split(pos, update = False)
        #Create the new code element
        codeelement = etree.Element('ipython-block',logid=self.currentlog)
        #Delete the last element of self.currentlog from the sheet 
        log = self.doc.logs[self.currentlog]
        key = (self.currentlog, log.lastcell.number, 'input')
        value = self.cell2sheet[key]
        while len(value)>0:
            blk, position = value[0]
            self.DeleteElement(blk,position,update = False)
        #insert the last element in codeelement
        codeelement.append(etree.Element('ipython-cell',type='input',\
                                         number = str(key[1])))
        #set newtext at the tail
        codeelement.tail = newtext
        #get the index in the <sheet> element where we must insert the new cell
        id = block.index
        l = len(self.celllist)
        while id<l:
            try:
                self.celllist[id].log
            except:
                id+=1
            else:
                break
        print 'new element:' #dbg
        etree.dump(codeelement) #dbg
        if id==l: #we must append the new element at the end of <sheet>
            index = len(self.element)
            self.element[index:index] = [codeelement]
        else:
            #insert the new code element 
            index = getindex(self.element,self.celllist[id].block)
            self.element[index:index] = [codeelement]
        #insert the new cells in celllist
        self.InsertCell('python',pos=block.index+1,update = False,\
                        ipython_block = codeelement)
        self.InsertCell('plaintext', pos = block.index+2, update = False,\
                        element = codeelement)
        print 'new sheet:' #dbg
        etree.dump(self.element) #dbg
        #update stuff. I could update only the modified cells, but I'm lazy
        self.Update(update,dicts = True)
        
    def InsertFigure(self, block, pos, figurexml, update = True):
        """Inserts the given figure at the given position in the given block.
        Returns the new block
        """
        
        fig_elem = etree.XML(figurexml)
        #Figure out where to insert the figure, according to the type of the
        #block
        
        if block.type == 'python':
            #This is a python block. Then if pos points to the position after
            #the end of the block, insert the figure after the block. If not
            #split the block and insert the figure at the given position.
            index = getindex(self.element, block.block)
            if pos >= len(block): # here we are using the __len__ method
                #Insert the xml in the sheet
                self.element[index+1:index+1] = [fig_elem]
                #Fix the text after the given element
                if self.celllist[block.index+1].type == 'plaintext':
                    textblock = self.celllist[block.index+1]
                    fig_elem.tail = textblock.GetText()
                    textblock.element = fig_elem
                #Insert in the view
                figcell = self.InsertCell('figure', pos = block.index+1,\
                                          update = False, element= fig_elem)
                self.Update(update = update, dicts = True)
            else: #We have to split the given block
                #Get the XML for the new ipython-block
                nextblock = block.Split(pos)
                #update the old text cell to point to the new block
                oldtextcell = self.celllist[block.index+1]
                if oldtextcell.type == 'plaintext':
                    nextblock.tail = oldtextcell.GetText()
                    oldtextcell.element = nextblock
                #insert nextblock in the sheet
                self.element[index+1:index+1] = [nextblock]
                self.InsertCell('python',pos = block.index+1, update = False, \
                                ipython_block = nextblock)
                #insert the figure
                self.element[index+1:index+1] = [fig_elem]
                figcell = self.InsertCell('figure', block.index+1,\
                                          update = False, element = fig_elem)
                #update
                self.Update(update = update, dicts = True)
            return figcell
        else:
            raise NotImplementedError

