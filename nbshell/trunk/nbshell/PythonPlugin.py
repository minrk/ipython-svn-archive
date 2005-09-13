#*****************************************************************************
#       Copyright (C) 2005 Tzanko Matev. <tsanko@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#
#  The Shell class was initially copied verbatim from the PyCrust project
#*****************************************************************************

from nbshell import Release
__author__  = '%s <%s>' % Release.author
__license__ = Release.license
__version__ = Release.version


import os
import sys
import StringIO

import wx

#from wx.py.version import VERSION

from lxml import etree

from notabene import notebook

from nbshell.utils import *
from nbshell.PythonWidget import Shell


def GetPluginFactory():
    """ Returns the factory object for the plugin. This function is called
    at the start of the program and should be called only once.
    """
    return PythonPluginFactory()

class PythonPluginFactory(object):
    """ This class is responsible for creating the document and view parts of 
    a plugin. Also it has some functions giving information about the plugin.
    The reason this class exists is because the document and view classes of
    the program shouldn't care how plugin objects are created. For example all
    the plain text in the notebook could be contained a single object which is 
    returned every time the document class wants to get a new one."""
    
    string = "python"
    #def GetString(self):
    #    """ Returns the type string of the plugin. This is used when a notebook
    #    file is loaded. See notebookformat.txt for more info"""
    #    return "python"
    
    type = "raw"
    #def GetType(self):
    #    """ Returns the way data should be passed to the plugin. Currently
    #    supported types are "raw" and "encoded". See notebookformat.txt for 
    #    more info"""
    #    return "raw" #Probably only the python code plugin should be raw
        
    def CreateDocumentPlugin(self,document, element):
        """Creates the document part of the plugin. The returned object is 
        stored in ipgDocument.celllist and is responsible for storing and
        serialization of data.
        """
        return PythonDocumentPlugin(document, element)
    
    def CreateViewPlugin(self,docplugin, view):
        """ Creates a view plugin connected to the given document plugin and 
        the given view. The view plugin is responsible for creating windows,
        handling events, etc. In simple plugins the document and the view plugin
        may be the same object
        """
        
        #In the distant future I might need to create views of different type for
        #one doc plugin. For example for a LaTeX plugin I might create a view 
        #for previewing in the notebook widget and a view for editing the LaTeX
        #code in a separate window
        if view.type=="notebook":
            return PythonNotebookViewPlugin(docplugin, view)
        else:
            return None #Well here I should throw an exception, however I am 
                        #not supposed to get to this line for a long long time
#end GenericPluginFactory


class PythonDocumentPlugin(object):
    def __init__(self, document, element):
        """Initialization. element is a Elemtent object holding a
        <ipython-block> tag"""
        self.document = document
        self.sheet = document.sheet
        self.element = element
        self.logid = self.element.get('logid', 'default-log') 
        self.log = document.logs[self.logid]
        self.notebook = document.notebook
        
        self.index = None   #Set by AddCell, InsertCell, DeleteCell
        self.view = None    #This plugin is designed for a single view. For
                            #multiple views there should be some modifications
        #print "block:" #dbg
        #etree.dump(self.element) #dbg
        self.cells = [self.log.log[int(x.attrib['number'])] for x in element]
        #[self.notebook.add_cell(int(x.attrib['number']),self.logid)
        #for x in self.element]
        
    type = 'python'
    
    def get_xml_text(self):
        return etree.tostring(self.element, encoding = 'utf-8')

    def __len__ (self):
        return len(self.element)
    
    def Clear(self):
        """Clears all data"""
        self.element.clear()
        self.element.attrib['logid'] = self.logid
        self.cells = []
        self.view.Update()
        
    def SetSavePoint(self):
        self.view.SetSavePoint()
    def IsModified(self):
        return self.view.modified
    modified = property(fget = IsModified)

    
    def GetStuff(self, id): #TODO: a better name
        """Returns a tuple (type, elem) where type is the type of the id'th
        element in self.element and elem is the the corresponding element in the
        cell in the log"""
        
        #print "id -> %s"%(str(id),) #dbg
        type = self.element[id].attrib['type']
        #print "type-> %s"%(type,) #dbg
        return (type, self.cells[id].element.find(type))
    
    def Split(self, pos, update = True):
        """Splits the block at the given position. Returns a <ipython-block>
        element with the remaining data. If update is True, updates the view.
        """
        
        root = etree.Element('ipython-block', logid = self.logid)
        for elem in self.element[pos:]:
            root.append(elem)
        del self.element[pos:]
        del self.cells[pos:]
        #TODO: spagetti
        self.sheet.Update(dicts = True, update = update)
        return lambda p:\
            self.sheet.InsertCell('python', p, update = False, element = root)
    
    def Concat(self, block, update = True):
        """Appends data in 'block' in the current block. If the operation was
        successful, return True, else return False"""
        assert block.type == 'python'
        if self.logid == block.logid:
            l = len(self.element)
            self.element[l:l] = block.element
            self.cells.extend(block.cells)
            if update:
                self.view.Update()
            return True
        return False

    def GetFactory(self):
        return PythonPluginFactory()

class PythonNotebookViewPlugin(object):
    def __init__(self, docplugin, view):
        """Initialization"""
        self.view = view
        self.doc = docplugin
        self.doc.view = self
        self.window = None
        #self.document = docplugin.document
        self.sheet = docplugin.sheet
        
        #used for setting selection
        self.start = -1
        self.end = -1
        #If self.sel_incell is True then the selection is part of one cell. If False, then
        #the selection consists of several cells
        self.sel_incell = False

        self.prompt_in_tpl = 'In [%s]: '
        self.prompt_out_tpl = 'Out[%s]: '
        
        self.hist_max_len = 666 #TODO: This must go in some configuration file
        self.history = [] #FIFO of at most self.hist_max_len strings
        self.hist_current = None #Index of the curret history item
        
    def add_to_history(self, line = None):
        """Adds the line to the history. If line is None gets the current line
        from the window"""
        if line is None:
            linenum = self.window.GetCurrentLine()
            line = self.window.GetLine(linenum)[self.promptlens[self.line2log[linenum][0]]:]
        
        if line: #We don't need empty lines
            self.history.append(line)
            l = len(self.history)
            if l > self.hist_max_len:
                del(self.history[0])
            self.hist_current = l-1
    
    def get_hist_item(self, dir= -1):
        """Gets the next previous line from the history if dir<0 or the next
        line if dir>0. If the history is empty return None"""

        dir = dir/abs(dir)
        if self.hist_current is None:
            return None
        self.hist_current+=dir
        l = len(self.history)
        if self.hist_current == l:
            self.hist_current = 0
        elif self.hist_current < 0:
            self.hist_current = l-1
        
        return self.history[self.hist_current]
    
    def hist_replace(self, dir):
        """Replaces the current line with prevoius (dir<0) or next (dir>0)
        line from the history"""
        
        t = self.get_hist_item(dir)
        if not t:
            return
        
        pos = self.window.GetCurrentPos()
        linenum = self.window.LineFromPosition(pos)

        if not self.CanEdit(pos = pos, line = linenum):
            return None

        startpos = self.window.PositionFromLine(linenum) +\
                 self.promptlens[self.line2log[linenum][0]]
        endpos = self.window.GetLineEndPosition(linenum)

        self.window.SetTargetStart(startpos)
        self.window.SetTargetEnd(endpos)
        self.window.ReplaceTarget(t)


    def SetFocus(self):
        if self.window is not None:
            self.window.SetFocus()
            
    def GetFirstId(self):
        """ This view is responsible for a list of consequent windows in the
        #notebook widget. GetFirsId returns the id of the first window"""
        return self.id
        
    def GetLastId(self):
        """See the description of GetFirstId"""
        return self.id
        
    #self.position is a property which gives the index in self.doc.element of
    #the ipython-cell on which the cursor currently is.
    def __get_position(self):
        pos = self.window.GetCurrentPos()
        linenum = self.window.LineFromPosition(pos)
        if pos == self.window.GetLength():
            return len(self.doc.element)
        elif self.line2log[linenum] is not None:
            return self.line2log[linenum][0]
        else:
            l = len(self.line2log)
            while linenum<l and self.line2log[linenum] is None:
                linenum +=1
            if linenum == l:
                return len(self.doc.element)
            else:
                return self.line2log[linenum][0]
            
    def __set_position(self, pos):
        if pos == self.position:
            return
        self.SetPosition(pos)
        
    position = property(fget = __get_position, fset = __set_position)
    length = property(fget = lambda self:len(self.doc))

    def SetPosition(self, pos):
        """Moves the cursor to the start of the element with the given id.
        Should be used only for input cells, because the output cells cannot be edited"""
        #TODO: this algorithm is slow. I check each line of the text if it is the start
        # of the element I need to go to. There should be a faster way to do this
        if pos == 0:
            self.window.GotoPos(self.PromptLen(0))
            return
        i = 0
        for i in range(len(self.line2log)):
            item = self.line2log[i]
            if item is not None and item[0] == pos:
                break
        
        self.window.GotoPos(self.window.PositionFromLine(i)+self.PromptLen(i))

    def __set_focus(self,event):
        self.doc.sheet._currentcell = self.doc
        event.Skip()

    def createWindow(self):
        """Creates the widget for displaying the code. Does nothing if it is
        already created"""
        if self.window is not None:
            return self.window
        #1. Create the window
        self.window = Shell(self, self.view, -1)
        wx.EVT_SET_FOCUS(self.window, self.__set_focus)
        #print "getting id" #dbg
        self.id = self.window.GetId()
        #print "id:", self.id #dbg
        #self.window.view = self
        #2. Add the window at the correct place in the notebook widget
        if self.doc.index == 0: #put the window at the beginning of the document
            #print "inserting cell" #dbg
            self.view.InsertCell(self.window, 0, update=False)
        else:
            #print "adding cell" #dbg
            prevcell = self.sheet.GetCell(self.doc.index-1)
            viewplugin = prevcell.view
            #print self.doc.index #dbg
            #print viewplugin #dbg
            lastid = viewplugin.GetLastId()
            #print lastid #dbg
            index = self.view.GetIndex(lastid)+1
            self.view.InsertCell(self.window, index, update = False)
        #3. Create line2log
        self.line2log = list()
        return self.window

        
    def Update(self):
        """ This method is required for all view implementations. It must
        update the view plugin.
        
        Remark: In order to update the view you must also call the Update
        method of the view after you call the Update method of the view 
        plugin. This is made so for efficiency. For example In the notebook
        view when you update a document cell you will probably need to call 
        RelayoutCells. So if you call Update on each document cell and call 
        RelayoutCells in each update this would be really inefficient.
        """
        if self.window is None: #then this is the first time Update is called
            self.createWindow()

        # Set the text in the window
        #TODO: It is really stupid to rewrite the text for 
        #every little change that can occur. Think of a way to avoid this
        cells = self.doc.cells
        block = self.doc.element
        #print "data->", data #dbg
        
        #log = self.doc.log
        #print "log->", log.log #dbg
        #self.window.ClearAll()
        self.line2log = []
        # local optimization
        l2l_append = self.line2log.append
        #oldlinecnt = 1 # = self.window.GetLineCount()
        last = len(cells) -1
        # Here we set up the text which will be displayed in the window
        outtext = StringIO.StringIO()
        #self.promptlen[i] holds the length of the prompt of cell i
        self.promptlens = []
        for i, cell in enumerate(cells):
            number =  cell.number
            #print 'i-> %d'%(i,) #dbg
            type, elem = self.doc.GetStuff(i)
            #print 'Result form GetStuff' #dbg
            #print type #dbg
            #print elem #dbg
            #etree.dump(elem) #dbg
            text = elem.text[1:] #The first symbol is '\n'
            if type == 'input':
                prompt = self.prompt_in_tpl % number
            elif type == 'output':
                prompt = self.prompt_out_tpl % number
            else :
                prompt = ""

            #print 'text -> %s'%text #dbg
            #print 'i -> %d, cell -> %s'%(i, str(cell)) #dbg
            lines = text.splitlines(True)
            if not lines:
                lines = ['']

            tmp = 0
            if i == last:
                lines[-1] = lines[-1][:-1] #without the last \n
                tmp = 1

            #print 'lines -> %s'%str(lines) #dbg
            outtext.write('\n' + prompt + lines[0])
            if type == 'input':
                prompt = '.' * (len(prompt)-1)+' ' #secondary prompt
            else:
                prompt = ''
            for line in lines[1:]:
                outtext.write(prompt + line)
            #linecnt =  
           
            #set up line2log. The first line is an empty one
            l2l_append(None)
            for j in range(len(lines)):
                l2l_append((i, j+1))
            
            #set up self.promptlens
            self.promptlens.append(len(prompt))
                #print "i -> %s, id->%s, type->%s, text->%s"%(str(i), str(id), str(type), str(text))
            #oldlinecnt = linecnt
        #if we have no cells we must set line2log here
        if not self.line2log:
            #StyledTextCtrl always has at least one line. If we added no
            #cells, self.line2log would be empty, so it would be inconsistant
            #with the displayed window. That's why we append None here
            l2l_append(None) #the window always has at least one line

        #TODO: uncomment this when I fix the problems with
        #updating the cursor position 
        #else:
            #self.line2log.append(None) #append ane
            #empty line at the end outtext.write('\n')
        self.window.SetText(outtext.getvalue())
        self.window.GotoPos(self.window.GetTextLength())
        #print "line2log->", self.window.line2log #dbg

    def SetSavePoint(self):
        if self.window is not None:
            self.window.SetSavePoint()
    
    def IsModified(self):
        if self.window is not None:
            return self.window.GetModify()
        else:
            return False
    modified = property(fget = IsModified)

    def GetPrompt(self, type, number, first = True):
        """Returns the prompt string for a cell with the given type and
        number. If first is True returns the prompt for the first line."""

        #print 'GetPrompt!'  # dbg
        if type not in ['input', 'output']:
            return ''
        if type == 'input':
            text = self.prompt_in_tpl % number
        else:
            text = self.prompt_out_tpl % number
        if not first:
            text = '.'*(len(text)-1)+' '
        return text

    def PromptLen(self, linenum):
        """Returns the lenght of the prompt that is on the given line."""
        
        line = self.line2log[linenum]
        if line is None: #a separator line
            return 0
        return self.promptlens[line[0]]
        #if line[1] != 1: #currently only the first line of a block is indented and has a prompt
        #    return 0
        
        #get the number of digits of the number of the input
        #item = self.doc.element[line[0]]
        #type = self.doc.GetStuff(line[0])[0]
        #strnumber = item.attrib['number']
        #return len(self.GetPrompt(type, strnumber, line[1] == 1))
    
    def UpdateDoc(self):
        """Updates the document to the current text in the widget. This method is
        run whenever the user presses Enter. We assume here that the only thing that might
        change is text inside the cells, so this is the only thing we change"""
        #Do nothing. 
        return
        for (i, cell)  in enumerate(self.doc.cells):
            type = self.doc.GetStuff(i)[0]
            cell.element.find(type).text = '\n'
        
        for i, line in enumerate(self.line2log):
            if line is None: #separator
                self.window.GetLine(i)
                continue
            promptlen = self.PromptLen(i)
            linetext = self.window.GetLine(i)[promptlen:]
            if linetext == "":
                linetext = '\n'
            elif linetext[-1]!='\n':
                linetext = linetext + '\n'

            elem = self.doc.GetStuff(line[0])[1]
            elem.text += linetext

    def ProcessLine(self, flag = False):
        """Process the line of text at which the user hits Enter."""
        linenum = self.window.GetCurrentLine()
        #print "linenum->", linenum #dbg
        item = self.line2log[linenum]
        if item is None:# we are in a empty separator line so do nothing
            return
        doc_id = item[0]
        (type, elem) = self.doc.GetStuff(doc_id)
        if type not in ['input', 'special']:
            #This is an output element so do nothing
            return
        
        #Retrieve the text of the input
        startline = linenum - item[1] + 1 #the counting of lines starts from 1
        #promptlen is the same for all lines in one input
        promptlen = self.PromptLen(linenum) 
        text = '\n'
        i = startline
        l = len(self.line2log)
        while i<l and self.line2log[i] is not None and \
              self.line2log[i][0] == item[0]:
            linetext = self.window.GetLine(i)[promptlen:]
            if linetext == '' or linetext[-1] !='\n':
                linetext = linetext + '\n'
            text = text + linetext
            i+=1

        #Get the cell corresponding to the element
        oldcell = self.doc.cells[doc_id]
        lastcell = self.doc.log.lastcell
        
        if oldcell.element == lastcell.element:
            #write text to the log
            lastcell.input = text #TODO: add special input support

            #This is the last cell of the log
            #try to run the current input. If it needs more, insert a line and continue editing
            if self.doc.log.Run(): # we have run the text and generated output
                #Update the sheet
                newblock = self.doc.sheet.UpdateOutput(self.doc.logid,\
                                self.doc.cells[doc_id], update = True)
                if newblock == None:
                    newblock = self.doc
                #Create a new input and append it at the end of the block
                cell = self.doc.log.Append("\n\n") #each input starts and ends with a newline
                self.doc.sheet.InsertElement(newblock, 'input', cell, update = True)
            else: #We need more input, do nothing
                # Delete the input from lastcell
                lastcell.input = '\n\n' #TODO: special input
        else:
            #This cell is not the last one in the log
            #write text to the log
            oldcell.input = text #TODO: add special input support
            if flag:
                cellstorun = self.doc.log.log[oldcell.number:-1] #omit the last cell
            else:
                cellstorun = [oldcell]
            self.doc.sheet.RerunCells(self.doc.log.logid, cellstorun, update = True)
                    
    def InsertText(self):
        """Inserts a text cell after the current line"""
        linenum = self.window.GetCurrentLine()
        #find the last input we will keep in the old cell
        while linenum>=0 and self.line2log[linenum] is None:
            linenum -= 1
        if linenum < 0 :
            #we did not find a previous cell, so do nothing
            return
        else:
            pos = self.line2log[linenum][0]
            if pos == len(self.doc.element) -1:
                #this block has only one cell, so do nothing
                return
            #call sheet.InsertText
            self.doc.sheet.InsertText(self.doc, pos+1, update = True)

    def GetLineType(self, linenum):
        """Returns the type of the line with number linenum.

        Return values:
            None - if it is a separator line
            0 - if it is an input line
            1 - if it is an output line
            
        The return codes are strange, but I want them to match to the values
        of self.line2log and self.doc.data"""
        #print "linenum: %d\n line2log: %s"%(linenum, str(self.line2log)) #dbg
        item = self.line2log[linenum]
        if item == None:
            return None
        else:
            return self.doc.data[item[0]][1]
    
    def CanEditLine(self, line):
        """Returns if the given line is editable"""
        #print "line -> %d"%(line,) #dbg
        #print 'line2log -> %s'%(str(self.line2log),) #dbg
        id = self.line2log[line]
        if id is None:
            return False
        id = id[0]
        #Check if the number of the current cell is the number of the last cell in the log.
        #if self.doc.cells[id].number == int(self.doc.log.log[-1].attrib['number']) \
        #   and self.doc.GetStuff(id)[0] == 'input':
        #    return True
        #else:
        #    return False
        #Check if the current cell is an input cell
        return self.doc.element[id].attrib['type'] in ['input', 'special']
    
    def CanEdit(self, oper = 'insert', pos = None, line = None):
        """Return true if the given editing operation should succeed at the
        given position if pos is None use the current position. oper can be
        one of: 'insert', 'delete', and 'backspace'"""
        #TODO: why we need to know anythong about the selection here
        #if self.GetSelectionStart() != self.GetSelectionEnd():
        #    if self.GetSelectionStart() >= self.promptPosEnd \
        #           and self.GetSelectionEnd() >= self.promptPosEnd:
        #        return True
        #    else:
        #        return False
        #else:
        #    return self.GetCurrentPos() >= self.promptPosEnd
        
        pos = pos or self.window.GetCurrentPos()
        #This is for optimization 
        line = line or self.window.LineFromPosition(pos)
        l2l = self.line2log
        #Check if the current line is editable. self.CanEditLine does the same
        #as the code below. It is not called for optimization
        id = l2l[line]
        if id is None:
            return False
        id = id[0]
        if not self.doc.element[id].attrib['type'] in ['input', 'special']:
            return False

        #Check if the cursor is in the prompt
        startpos = self.window.PositionFromLine(line)
        promptlen = self.PromptLen(line)
        if startpos + promptlen > pos:
            return False
        
        #If the operation is delete and the cursor is at the end of the line 
        if oper == 'delete' and self.window.GetCharAt(pos) == ord('\n'):
            #Check if the next line belongs to the same input
            l = len(l2l)
            return (line +1 < l and l2l[line+1] is not None and
                l2l[line+1][0] == l2l[line][0])
        elif oper == 'backspace':
            #Check if this is the first line
            return pos > startpos + promptlen or l2l[line][1] > 1
        else:
            return True


    def InsertLineBreak(self, pos = None):
        """Insert a new line break. Does not check if the current position is
        editable, so you should call self.window.CanEdit() before calling this
        method."""
        
        if pos is None:
            pos = self.window.GetCurrentPos()
        
        linenum = self.window.LineFromPosition(pos)
        item = self.line2log[linenum]
        if item is None:
            #This is a separator line. Insert a new separator line after it
            self.window.InsertText(pos,'\n')
            self.line2log[linenum:linenum] = [None]
        else:
            #Check if we are inside the prompt
            elem = self.doc.element[self.line2log[linenum][0]]
            type = elem.attrib['type']
            number = elem.attrib['number']
            prompt = self.GetPrompt(type, number, False)
            promptlen = len(prompt)
            startpos = self.window.PositionFromLine(linenum)
            if pos - startpos < promptlen:
                #Do nothing
                return
            #else:

            #Insert a newline and update line2log
            line = self.window.GetLine(linenum)
            if line[-1] == '\n':
                line = line[:-1]
            i = promptlen
            l = len(line)
            while i<l and line[i].isspace():
                i+=1
            header = '\n' + prompt + line[promptlen:i]
            # Insert the new line and set the cursor at its beginning
            self.window.InsertText(pos, header)
            self.window.GotoPos(pos + len(header)) 
            # Update line2log
            self.line2log[linenum+1:linenum+1] = [(item[0], item[1]+1)]
            i = linenum+2
            l = len(self.line2log)
            while i<l and self.line2log[i] is not None and\
                  self.line2log[i][0] == item[0]:
                self.line2log[i] = (item[0], self.line2log[i][1]+ 1)
                i+=1

    def _next_pos(self, pos, dir =1):
        """The pos must be editable. If dir=1 returns the next editable
        position, or None if pos is the last editable position. If dir = -1.
        returns the prevous editable position or None
        """
        
        assert self.CanEdit(pos = pos)
        line = self.window.LineFromPosition(pos)
        if dir == 1:
            #get the next position

            if self.window.GetCharAt(pos) != ord('\n'):
                return pos+1
            l = len(self.line2log)
            #if this is not the last line of the input
            if (line + 1 < l and self.line2log[line+1] is not None and
                self.line2log[line+1][0] == self.line2log[line][0]):
                return pos + 1 +self.PromptLen(line+1)
            else:
                #This is the last line
                return None
        else:
            #get the previous position
            startpos = self.window.PositionFromLine(line)
            promptlen = self.PromptLen(line)
            return ifelse(pos>startpos + promptlen,\
                          pos-1,#we are not at the start of the line
                          ifelse(self.line2log[line][1]>1,\
                                 startpos -1,#we are at the start and this is not the first line
                                 None))#we are at the start and this is the first line

    def Delete(self, pos = None, forward = True):
        """Called when the user wants to delete a character at the current
        position. If forward is true deletes the character at the current
        position. If forward is False deletes the character before the position"""
        
        pos = pos or self.window.GetCurrentPos()
        oper = ifelse(forward, 'delete', 'backspace')
        if not self.CanEdit(oper, pos = pos):
            return
        dir = ifelse(forward, 1, -1)
        
        nextpos = self._next_pos(pos, dir)
        if nextpos is None:
            return None
        pos, nextpos = min(pos, nextpos), max(pos, nextpos)
        #Delete the characters
        self.window.SetTargetStart(pos)
        self.window.SetTargetEnd(nextpos)
        self.window.ReplaceTarget('')
        #If we deleted a line update self.line2log
        if pos+1<nextpos:
            i = self.window.LineFromPosition(pos) +1
            del(self.line2log[i])
            l = len(self.line2log)
            while (l<l and self.line2log[i] is not None and
                   self.line2log[i][0] == self.line2log[linenum][0]):
                i+=1
                self.line2log[i][1] -= 1

    def SetSelection(self):
        """If the user is trying to select anything SetSelection will move the
        current anchor and position so that the user can only select either a part of one
        <ipython-cell> object or whole <ipython-cell> objects
        """
        (start, end) = self.window.GetSelection()
        if start == end: #We have not selected anything
            self.start = start
            self.end = end
            return
        if (start, end) == (self.start, self.end):
            #We have already set up the selection
            return
        #print '(start, end) -> (%d, %d)'%(start,end) #dbg
        #print '(anchor, pos) -> (%d, %d)'%\
        #      (self.window.GetAnchor(),self.window.GetCurrentPos()) #dbg
        startline = self.window.LineFromPosition(start)
        endline = self.window.LineFromPosition(end)
        #Check if the start and the end point are in one cell
        if (self.line2log[startline] is not None and self.line2log[endline] is not None and
            self.line2log[startline][0] == self.line2log[endline][0]):
            (self.start, self.end) = (start,end)
            self.sel_incell = True
            return
        
        #if startline is None, we do nothing. If not, we move startline
        #to be the first line of the current element
        while self.line2log[startline] is not None and\
              self.line2log[startline][1] > 1:
            startline -= 1
        self.start = self.window.PositionFromLine(startline)
        #while we have not reached the end of the document, and the next line
        #corresponds to the same element as the current line move forward
        l = len(self.line2log)
        while endline < l-1 and self.line2log[endline] is not None and\
              self.line2log[endline+1] is not None:
            endline += 1
        self.end = self.window.GetLineEndPosition(endline)
        if self.window.GetAnchor() == start:
            self.window.SetAnchor(self.start)
            self.window.SetCurrentPos(self.end)
        else:
            self.window.SetAnchor(self.end)
            self.window.SetCurrentPos(self.start)
        self.sel_incell = False
        #print 'new'
        #print '(start, end) -> (%d, %d)'%(self.start,self.end) #dbg
        #print '(anchor, pos) -> (%d, %d)'%\
        #      (self.window.GetAnchor(),self.window.GetCurrentPos()) #dbg
            
    def DeleteSelf(self):
        """Delete current cell"""
        self.doc.sheet.DeleteCell(self.doc)
        
    def Close(self, update = True):
        index = self.view.GetIndex(self.id)
        self.view.DeleteCell(index, update)
        
    def Copy(self):
        """Copies the selection to the clipboard"""
        #Get the selection
        (start, end) = self.window.GetSelection()
        if (start, end) != (self.start, self.end):
            self.SetSelection()
            
        (start, end) = min(self.start, self.end), max(self.start, self.end)
        startline = self.window.LineFromPosition(start)
        endline = self.window.LineFromPosition(end)

        #Decide what types of data objects we are going to create
        #There are three types of objects:
        #    * raw text - used for pasting to a text cell
        #    * code text - raw text having the prompts stripped. Used
        #      for pasting code in a code cell
        #    * a list of cells - used for pasting cells in a code block
        rawtext, codetext, codecell = True, False, False
        codetext = True #We always make this object now
        
        if (self.line2log[startline] is None or self.line2log[endline] is None or
            self.line2log[startline][0] != self.line2log[endline][0]):
            #Don't include code 
            codecell = True
        elif (self.line2log[startline][1] == 1 and 
              start == self.window.PositionFromLine(startline) and 
              (endline == len(self.line2log) - 1 or 
               (self.line2log[endline+1] is None or 
                self.line2log[endline+1][1] == 1 and
                end == self.window.LineLength(endline) +\
                self.window.PositionFromLine(endline)))):
            codecell = True
        
        #Now get the data
        #rawtext is always true,
        text = self.window.GetTextRange(start, end)
        dataobj = wx.DataObjectComposite()
        rawobj = wx.TextDataObject(text)
        dataobj.Add(rawobj, True)

        if codetext:
            #Strip text from prompts. We handle the first line separately, because
            #we don't know if the whole one is selected
            s = self.window.PositionFromLine(startline)
            s += self.PromptLen(startline)
            if s > start: #start is inside the prompt
                text = text[s-start:] #strip the prompt
                
            #strip all the other prompts
            lines = text.splitlines(True)
            for i in range(1,len(lines)):
                lines[i] = lines[i][self.PromptLen(startline+i):]
            text = ''.join(lines)
            codeobj = wx.CustomDataObject('nbCode')
            codeobj.SetData(str(text)) #TODO:text is unicode and SetData does not support it
            dataobj.Add(codeobj)
        
        if codecell:
            #Get all the cells and generate xml from them. It will be used to
            #copy the new cells
            
            xmltext = StringIO.StringIO()
            xmltext.write(u'<ipython-block logid="%s">'%self.doc.logid)
            for line in self.line2log[startline:endline+1]:
                if line is not None and line[1] == 1: #This is the first line of the cell
                    xmltext.write(etree.tostring(self.doc.element[line[0]], 'utf-8'))
            xmltext.write(u'</ipython-block>')
            cellobj = wx.CustomDataObject('nbCell')
            cellobj.SetData(str(xmltext.getvalue())) #TODO: fix unicode problem
            dataobj.Add(cellobj)
            xmltext.close()
        
        #Finally, copy to clipboard
        if wx.TheClipboard.Open():
            wx.TheClipboard.Clear()
            wx.TheClipboard.AddData(dataobj)
            wx.TheClipboard.Flush()
            wx.TheClipboard.Close()
            return True
        else:
            return False
        
    
    def Paste(self, pos = None):
        """Gets the copied object from the clipboard and inserts it at
        position 'pos' or at the current position if pos is None. pastes
        it."""
        
        if pos is None:
            pos = self.window.GetCurrentPos()
            
        linenum = self.window.LineFromPosition(pos)
        cellobj, codeobj = wx.CustomDataObject('nbCell'), wx.CustomDataObject('nbCode')
        textobj = wx.TextDataObject()
        rawtext, codetext, codecell = (False,)*3
        #Get the data
        if not wx.TheClipboard.Open():
            return
        if self.line2log[linenum] is None: 
            #we are between cells
            if wx.TheClipboard.IsSupported(wx.CustomDataFormat('nbCell')):
                codecell = True
                wx.TheClipboard.GetData(cellobj)
        else:
            #we are inside a cell. 
            if wx.TheClipboard.IsSupported(wx.CustomDataFormat('nbCode')):
                codetext = True
                wx.TheClipboard.GetData(codeobj)
            #if we are at the last character in the cell and there is a nbCell object
            #elif ((len(self.line2log) -1 == linenum or #if linenum is the last line in the cell
            #       self.line2log[linenum+1] is None or
            #       self.line2log[linenum+1][0] != self.line2log[linenum][0]) and
            #      #and caret is at the end of the line
            #      pos == self.window.PositionFromLine(linenum) +\
            #             self.window.LineLength(linenum)):
            #    linenum += 1 #this will be the place where we paste the cells
            #    wx.TheClipboard.GetData(cellobj)
            #    codecell = True
            elif (wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_TEXT)) or
                  wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_UNICODETEXT))):
                rawtext = True
                wx.TheClipboard.GetData(textobj)
        wx.TheClipboard.Close()
        #paste
        if rawtext:
            self.InsertTextInCell(pos, textobj.GetText())
        elif codetext:
            self.InsertTextInCell(pos, codeobj.GetData())
        elif codecell:
            xml = cellobj.GetData()
            #print xml, type(xml) #dbg
            elem = etree.XML(xml)
            if elem.attrib['logid'] != self.doc.logid:
                return
            
            l = len(self.line2log)
            while linenum<l and self.line2log[linenum] is None:
                linenum+=1
            if linenum == l:
                pos = len(self.doc.element)
            else:
                pos = self.line2log[linenum][0]
            for ipcell in elem:
                number = int(ipcell.attrib['number'])
                tp = ipcell.attrib['type']
                cell = self.doc.log.Get(number)
                self.doc.sheet.InsertElement(self.doc, tp, cell, pos, update = False)
                pos+=1
            self.Update()
        else:
            return
                

    def InsertTextInCell(self, pos, text):
        """Inserts the given text at the given position. The position must be editable"""
        if not self.CanEdit(oper='insert', pos=pos):
            return
        lines = text.splitlines(False)
        last_newline = False
        if text[-1] == '\n':
            last_newline = True
        linenum = self.window.LineFromPosition(pos)
        #We assume here that all prompts have equal length in a cell
        promptlen = self.PromptLen(linenum) 
        l = len(lines)
        for i, line in enumerate(lines):
            self.window.SetTargetStart(pos)
            self.window.SetTargetEnd(pos)
            self.window.ReplaceTarget(line)
            pos+=len(line)
            if i<l-1 or last_newline: #The last line may not finish with '\n'
                self.InsertLineBreak(pos)
            pos += 1 + promptlen
            
    def DeleteSelection(self):
        """Deletes the code or cells in the selection"""
        
        #Currently can delete only whole cells
        
        #Get the selection
        (start, end) = self.window.GetSelection()
        if (start, end) != (self.start, self.end):
            self.SetSelection()
            
        (start, end) = min(self.start, self.end), max(self.start, self.end)
        startline = self.window.LineFromPosition(start)
        endline = self.window.LineFromPosition(end)

        #If the start and end line are not in the same cell
        if ((self.line2log[startline] is None or self.line2log[endline] is None or
             self.line2log[startline][0] != self.line2log[endline][0]) or\
            #or the selection covers one whole cell
            (self.line2log[startline][1] == 1 and 
             start == self.window.PositionFromLine(startline) and 
             (endline == len(self.line2log) - 1 or 
              (self.line2log[endline+1] is None or 
               self.line2log[endline+1][1] == 1 and
               end == self.window.LineLength(endline) +\
               self.window.PositionFromLine(endline))))):
            #Get all the selected cells and delete them
            while self.line2log[startline] is None:
                startline +=1
            while self.line2log[endline] is None:
                endline -= 1
            startpos = self.line2log[startline][0]
            endpos = self.line2log[endline][0]
            
            for pos in reversed(range(startpos, endpos+1)):
                self.doc.sheet.DeleteElement(self.doc, pos, update = False)
            self.Update()
        else: #Delete a part of a cell
            #If start is in the prompt move it after the prompt
            ls = self.window.PositionFromLine(startline)
            promptlen = self.PromptLen(startline)
            if ls+promptlen >= start:
                start = ls+promptlen
            #Make the same for end
            le = self.window.PositionFromLine(endline)
            if le+promptlen >= end:
                end = le + promptlen
                
            #Get the text and count the newlines
            nlcount = self.window.GetTextRange(start, end).count('\n')
            #Remove the text 
            self.window.SetTargetStart(start)
            self.window.SetTargetEnd(end)
            self.window.ReplaceTarget('')
            #fix line2log by removing the last nlcount lines for the current cell
            it = self.line2log[startline][0]
            lastline = startline
            l = len(self.line2log)
            while (lastline<l and self.line2log[lastline] is not None and
                   self.line2log[lastline][0] == it):
                lastline +=1
            del self.line2log[lastline-nlcount:lastline]
