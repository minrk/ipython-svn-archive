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
from wx import stc
from wx import py

from wx.py.buffer import Buffer
import wx.py.dispatcher
import wx.py.frame
from wx.py.pseudo import PseudoFileIn
from wx.py.pseudo import PseudoFileOut
from wx.py.pseudo import PseudoFileErr
#from wx.py.version import VERSION

from lxml import etree

from notabene import notebook

from nbshell import editwindow
from nbshell.utils import findnew

NAVKEYS = (wx.WXK_END, wx.WXK_LEFT, wx.WXK_RIGHT,
           wx.WXK_UP, wx.WXK_DOWN, wx.WXK_PRIOR, wx.WXK_NEXT)

def ifelse(a,b,c):
    if (a):
        return b
    else:
        return c

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
        """Initialization. ipython-block is a Elemtent object holding a
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
        #print "block:"
        #etree.dump(self.element) #dbg
        self.cells = \
        [notebook.NewCell(self.notebook.get_cell(int(x.attrib['number']),self.logid))
         for x in self.element]
        
    type = 'python'
    
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
        return PlainTextPluginFactory()

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
        #oldlinecnt = 1 # = self.window.GetLineCount()
        last = len(cells) -1
        # Here we set up the text which will be displayed in the window
        outtext = StringIO.StringIO()
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
                prompt = 'In[%d] '%number
            elif type == 'output':
                prompt = 'Out[%d] '%number
            else :
                prompt = ""

            #print 'text -> %s'%text #dbg
            #print 'i -> %d, cell -> %s'%(i, str(cell)) #dbg
            lines = text.splitlines(True)
            if lines == []:
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
            self.line2log.append(None)
            for j in range(len(lines)):
                self.line2log.append((i, j+1))
                #print "i -> %s, id->%s, type->%s, text->%s"%(str(i), str(id), str(type), str(text))
            #oldlinecnt = linecnt
        #if we have no cells we must set line2log here
        if len(self.line2log) == 0:
            self.line2log.append(None) #the window always has at least one line
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

    def PromptLen(self, linenum):
        """Returns the lenght of the prompt that is on the given line."""
        
        line = self.line2log[linenum]
        if line is None: #a separator line
            return 0
        
        #if line[1] != 1: #currently only the first line of a block is indented and has a prompt
        #    return 0
        
        #get the number of digits of the number of the input
        item = self.doc.element[line[0]]
        type = self.doc.GetStuff(line[0])[0]
        strnumber = item.attrib['number']
        if type == 'input':
            return len(strnumber) + 5 #In[ ] - 5
        elif type == 'output' and line[1] == 1: #indent only the first line of output
            return len(strnumber) + 6 #Out[ ] - 6
        else:
            return 0 #The other types of input don't have prompts for now
    
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

    def ProcessLine(self):
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
            if linetext == '':
                linetext = '\n'
            elif linetext[-1]!='\n':
                linetext = linetext + '\n'
            text = text + linetext
            i+=1

        #Get the cell corresponding to the element
        oldcell = self.doc.cells[doc_id]
        lastcell = self.doc.log.lastcell
        if oldcell.element == lastcell.element:
            #This is the last cell of the log
            #write text to the log
            elem = findnew(lastcell.element,type)
            elem.text = text
            #try to run the current input. If it needs more, insert a line and continue editing
            if self.doc.log.Run(): # we have run the text and generated output
                #Update the sheet
                newblock = self.doc.sheet.UpdateOutput(self.doc.logid,\
                                self.doc.cells[doc_id], update = True)
                if newblock == None:
                    newblock = self.doc
                #Create a new input and append it at the end of the block
                cell = self.doc.log.Append("\n\n") #each input starts and ends with a newline
                self.doc.sheet.InsertElement(newblock, 'input', cell, \
                                             update = True)
            else: #We need more input, do nothing
                # Delete the input from lastcell
                elem.text = '\n\n'
        else:
            #This cell is not the last one in the log
            #print self.line2log[linenum] #dbg
            #1.1.1 Put the input in the last cell
            elem = findnew(lastcell.element,type)
            elem.text = text
            #1.1.2. Run the last cell
            if self.doc.log.Run(): # we have run the text and generated output
                #Make a new last input
                cell = self.doc.log.Append("\n\n") #each input starts and ends with a newline
                #replace the old last input with the new one
                self.doc.sheet.ReplaceCells(self.doc.logid, lastcell,\
                                            self.doc.log.lastcell, update = False)
                #Replace the old cell with the new one (the old lastcell)
                self.doc.sheet.ReplaceCells(self.doc.logid,\
                                            oldcell, lastcell, update = False)
                #Delete oldcell
                self.doc.log.Remove(oldcell)
                #Update the sheet
                self.doc.sheet.UpdateOutput(self.doc.logid,
                                            self.doc.cells[doc_id], update = False)
                self.doc.sheet.Update()
                return
            else:
                #Remove the text from lastcell
                elem.text = '\n\n'
                    
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
    
    def CanEdit(self, line):
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
        if self.doc.GetStuff(id)[0] in ['input', 'special']:
            return True
        else:
            return False

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
            promptlen = self.PromptLen(linenum)
            startpos = self.window.PositionFromLine(linenum)
            if pos - startpos < promptlen:
                #Do nothing
                return
            #else:

            #Insert a newline and update line2log
            line = self.window.GetLine(linenum)
            i = promptlen
            l = len(line)
            while i<l and line[i].isspace():
                i+=1
            header = '\n' + ' '*(promptlen-4)+'... ' + line[promptlen:i]
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


    def SetSelection(self):
        """If the user is trying to select anything SetSelection will move the
        current anchor and position so that the user only selects whole
        <ipython-cell> objects
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

class Shell(editwindow.EditWindow):
    """Shell based on StyledTextCtrl."""

    name = 'Shell'
    #revision = __revision__ #TODO: fix

    def __init__(self,view, parent, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.CLIP_CHILDREN):
        """Create Shell instance."""
        editwindow.EditWindow.__init__(self, parent, id, pos, size, style)

        self.id = self.GetId()
        self.parent = parent
        self.view = view
        #self.document = view.doc
        #self.log = self.document.log
        self.line2log = [] # For each line in the window contains a tuple of
                           # the id of the corresponding part of the document and
                           # the corresponding line in the text in the log
                           #
                           # (id, n) -> the n'th line of document.data[id] 
        
        self.oldlineno = 1 # used by OnModified. Is there a way to
                           # declare this inside the method? Like a
                           # C++ static variable
        self.oldpos = (0,0)

        self.wrap()

        # Find out for which keycodes the interpreter will autocomplete.
        #self.autoCompleteKeys = self.document.log.interp.getAutoCompleteKeys()
        #TODO: fix this. IPython must tell us which keys go here
        self.autoCompleteKeys = []
        
        # Keep track of the last non-continuation prompt positions.
        #self.promptPosStart = 0
        self.promptPosEnd = 0
        # Keep track of multi-line commands.
        self.more = False
        # Create the command history.  Commands are added into the
        # front of the list (ie. at index 0) as they are entered.
        # self.historyIndex is the current position in the history; it
        # gets incremented as you retrieve the previous command,
        # decremented as you retrieve the next, and reset when you hit
        # Enter.  self.historyIndex == -1 means you're on the current
        # command, not in the history.
        #self.history = []
        #self.historyIndex = -1
        # Assign handlers for keyboard events.
        wx.EVT_CHAR(self, self.OnChar)
        wx.EVT_KEY_DOWN(self, self.OnKeyDown)
        # Assign handler for idle time.
        self.waiting = False
        wx.EVT_IDLE(self, self.OnIdle)
        stc.EVT_STC_MODIFIED(self, id, self.OnModified)
        stc.EVT_STC_UPDATEUI(self, id, self.OnUpdateUI)
        # Display the introductory banner information.
        #self.showIntro(introText) #TODO: remove this
        # Assign some pseudo keywords to the interpreter's namespace.
        #self.setBuiltinKeywords() #TODO move in the view
        # Add 'shell' to the interpreter's local namespace.
        #self.setLocalShell()
        # Do this last so the user has complete control over their
        # environment.  They can override anything they want.
        #self.execStartupScript(self.interp.startupScript) #TODO: what does this button do?
        #wx.CallAfter(self.ScrollToLine, 0)

    def Resize (self, width = None):
        """ See StaticTextPlugin.Resize """
        if width is None:
            width = self.GetClientSizeTuple()[0]

        height = self.TextHeight(0)*self.GetLineCount() #works, because all lines have the same height
        self.SetClientSizeWH(width, height)

    def SetTheFocus(self, pos, start):
        """ Sets the focus to this cell """
        self.SetFocus()
        pos1 = tuple(self.PointFromPosition(self.GetCurrentPos()))
        self.parent.ScrollTo(self.view.doc.index, pos1) # show the highest pixel of the caret
        if start: #The focus came from the previous cell
            self.GotoPos(min(pos, self.GetLineEndPosition(0)))
        else: #The focus came from the next cell
            lastline = self.GetLineCount() - 1
            self.GotoPos(min(self.PositionFromLine(lastline) + pos, self.GetLineEndPosition(lastline)))
    
    def OnModified (self, evt):
        lineno = self.GetLineCount()
        if self.oldlineno != lineno :
            self.oldlineno = lineno
            self.parent.RelayoutCells(id = self.id)

    def OnUpdateUI (self, evt):
        editwindow.EditWindow.OnUpdateUI(self, evt)
        pos = tuple(self.PointFromPosition(self.GetCurrentPos()))
        if (pos != self.oldpos):
            self.parent.ScrollTo(self.view.doc.index, pos) # show the highest pixel of the caret
#            self.view.ScrollTo(self.cell.index, (pos[0], pos[1]+self.TextHeight(0))) # now show the lowest pixel.
            #TODO: If there is a way to make scrolling slower, I can't
            #think of it right now :)
            self.oldpos = pos

#    def destroy(self):
#        del self.interp

    def setFocus(self):
        """Set focus to the shell."""
        self.SetFocus()

    def OnIdle(self, event):
        """Free the CPU to do other things."""
        if self.waiting:
            time.sleep(0.05)
        
        self.view.SetSelection()
        event.Skip()

#    def showIntro(self, text=''):
#        """Display introductory text in the shell."""
#        if text:
#            if not text.endswith(os.linesep):
#                text += os.linesep
#            self.write(text)
#        try:
#            self.write(self.interp.introText)
#        except AttributeError:
#            pass

#TODO: Move this somewhere
#    def setBuiltinKeywords(self):
#        """Create pseudo keywords as part of builtins.
#
#        This sets `close`, `exit` and `quit` to a helpful string.
#        """
#        import __builtin__
#        __builtin__.close = __builtin__.exit = __builtin__.quit = \
#            'Click on the close button to leave the application.'

    def quit(self):
        """Quit the application."""

        # XXX Good enough for now but later we want to send a close event.

        # In the close event handler we can make sure they want to
        # quit.  Other applications, like PythonCard, may choose to
        # hide rather than quit so we should just post the event and
        # let the surrounding app decide what it wants to do.
        self.write('Click on the close button to leave the application.')

#    def setLocalShell(self):
#        """Add 'shell' to locals as reference to ShellFacade instance."""
#        self.interp.locals['shell'] = ShellFacade(other=self)

#TODO: Maybe I need this somewhere
#    def execStartupScript(self, startupScript):
#       """Execute the user's PYTHONSTARTUP script if they have one."""
#        if startupScript and os.path.isfile(startupScript):
#            text = 'Startup script executed: ' + startupScript
#            self.push('print %r; execfile(%r)' % (text, startupScript))
#        else:
#            self.push('')

#TODO: Make an about dialog and mention PyCrust there
#    def about(self):
#        """Display information about Py."""
#        text = """
#Author: %r
#Py Version: %s
#Py Shell Revision: %s
#Py Interpreter Revision: %s
#Python Version: %s
#wxPython Version: %s
#Platform: %s""" % \
#        (__author__, VERSION, self.revision, self.interp.revision,
#         sys.version.split()[0], wx.VERSION_STRING, sys.platform)
#        self.write(text.strip())

    def OnChar(self, event):
        """Keypress event handler.

        Only receives an event if OnKeyDown calls event.Skip() for the
        corresponding event."""

        # Prevent modification of previously submitted
        # commands/responses.
        if not self.CanEdit():
            return
        key = event.KeyCode()
        currpos = self.GetCurrentPos()
        stoppos = self.promptPosEnd
        # Return (Enter) needs to be ignored in this handler.
        if key == wx.WXK_RETURN:
            pass
        elif key in self.autoCompleteKeys:
            # Usually the dot (period) key activates auto completion.
            # Get the command between the prompt and the cursor.  Add
            # the autocomplete character to the end of the command.
            if self.AutoCompActive():
                self.AutoCompCancel()
            command = self.GetTextRange(stoppos, currpos) + chr(key)
            self.write(chr(key))
            if self.autoComplete:
                self.autoCompleteShow(command)
        #elif key == ord('('):
        #    # The left paren activates a call tip and cancels an
        #    # active auto completion.
        #    if self.AutoCompActive():
        #        self.AutoCompCancel()
        #    # Get the command between the prompt and the cursor.  Add
        #    # the '(' to the end of the command.
        #    self.ReplaceSelection('')
        #    command = self.GetTextRange(stoppos, currpos) + '('
        #    self.write('(')
        #    self.autoCallTipShow(command)
        else:
            # Allow the normal event handling to take place.
            event.Skip()

    def OnKeyDown(self, event):
        """Key down event handler."""

        key = event.KeyCode()
        # If the auto-complete window is up let it do its thing.
        if self.AutoCompActive():
            event.Skip()
            return
        # Prevent modification of previously submitted
        # commands/responses.
        controlDown = event.ControlDown()
        altDown = event.AltDown()
        shiftDown = event.ShiftDown()
        currpos = self.GetCurrentPos()
        endpos = self.GetTextLength()
        selecting = self.GetSelectionStart() != self.GetSelectionEnd()
        # Return (Enter) is used to insert a new line
        if not shiftDown and key == wx.WXK_RETURN:
            if self.CanEdit():
                self.view.InsertLineBreak()
        #Shift-Return, (Shift-Enter) is used to execute the current input
        elif shiftDown and key == wx.WXK_RETURN:
            if self.CallTipActive():
                self.CallTipCancel()
            self.view.ProcessLine()
        #Ctrl-I inserts a text cell
        elif controlDown and key in (ord('i'),ord('I')):
            self.view.InsertText()
        #Ctrl-D deletes the current cell
        elif controlDown and key in (ord('d'), ord('D')):
            self.view.DeleteSelf()
        # Ctrl+Return (Cntrl+Enter) is used to insert a line break.
        #elif controlDown and key == wx.WXK_RETURN:
        #    if self.CallTipActive():
        #        self.CallTipCancel()
        #    if currpos == endpos:
        #        self.processLine()
        #    else:
        #        self.insertLineBreak()
        # Let Ctrl-Alt-* get handled normally.
        elif controlDown and altDown:
            event.Skip()
        # Clear the current, unexecuted command.
        elif key == wx.WXK_ESCAPE:
            if self.CallTipActive():
                event.Skip()
        #    else:
        #        self.clearCommand()
        # Increase font size.
        elif controlDown and key in (ord(']'),):
            dispatcher.send(signal='FontIncrease')
        # Decrease font size.
        elif controlDown and key in (ord('['),):
            dispatcher.send(signal='FontDecrease')
        # Default font size.
        elif controlDown and key in (ord('='),):
            dispatcher.send(signal='FontDefault')
        # Cut to the clipboard.
        #elif (controlDown and key in (ord('X'), ord('x'))) \
        #or (shiftDown and key == wx.WXK_DELETE):
        #    self.Cut()
        # Copy to the clipboard.
        elif controlDown and not shiftDown \
            and key in (ord('C'), ord('c'), wx.WXK_INSERT):
            self.Copy()
        # Copy to the clipboard, including prompts.
        elif controlDown and shiftDown \
            and key in (ord('C'), ord('c'), wx.WXK_INSERT):
            self.CopyWithPrompts()
        # Copy to the clipboard, including prefixed prompts.
        elif altDown and not controlDown \
            and key in (ord('C'), ord('c'), wx.WXK_INSERT):
            self.CopyWithPromptsPrefixed()
        # Home needs to be aware of the prompt.
        elif key == wx.WXK_HOME:
            home = sum(self.getLineStart())
            if currpos > home:
                self.SetCurrentPos(home)
                if not selecting and not shiftDown:
                    self.SetAnchor(home)
                    self.EnsureCaretVisible()
            else:
                event.Skip()
        #
        # The following handlers modify text, so we need to see if
        # there is a selection that includes text prior to the prompt.
        #
        # Don't modify a selection with text prior to the prompt.
        elif selecting and key not in NAVKEYS and not self.CanEdit():
            pass
        # Paste from the clipboard.
        #elif (controlDown and not shiftDown and key in (ord('V'), ord('v'))) \
        #         or (shiftDown and not controlDown and key == wx.WXK_INSERT):
        #    self.Paste()
        # Paste from the clipboard, run commands.
        #elif controlDown and shiftDown and key in (ord('V'), ord('v')):
        #    self.PasteAndRun()
        # Replace with the previous command from the history buffer.
        #elif (controlDown and key == wx.WXK_UP) \
        #         or (altDown and key in (ord('P'), ord('p'))):
        #    self.OnHistoryReplace(step=+1)
        # Replace with the next command from the history buffer.
        #elif (controlDown and key == wx.WXK_DOWN) \
        #         or (altDown and key in (ord('N'), ord('n'))):
        #    self.OnHistoryReplace(step=-1)
        # Insert the previous command from the history buffer.
        #elif (shiftDown and key == wx.WXK_UP) and self.CanEdit():
        #    self.OnHistoryInsert(step=+1)
        # Insert the next command from the history buffer.
        #elif (shiftDown and key == wx.WXK_DOWN) and self.CanEdit():
        #    self.OnHistoryInsert(step=-1)
        # Search up the history for the text in front of the cursor.
        #elif key == wx.WXK_F8:
        #    self.OnHistorySearch()
        # Don't backspace over the latest non-continuation prompt.
        elif key == wx.WXK_BACK:
            if selecting and self.CanEdit():
                event.Skip()
            elif self.CanEdit('backspace'):
                event.Skip()
        # Only allow these keys after the latest prompt.
        elif key in (wx.WXK_TAB, wx.WXK_DELETE):
            if self.CanEdit():
                event.Skip()
        # Don't toggle between insert mode and overwrite mode.
        elif key == wx.WXK_INSERT:
            pass
        # Don't allow line deletion.
        elif controlDown and key in (ord('L'), ord('l')):
            pass
        # Don't allow line transposition.
        elif controlDown and key in (ord('T'), ord('t')):
            pass

        # Basic navigation keys should work anywhere.
        #If we pressed WXK_DOWN on the last line, or WXK_UP on the first line 
        #of the cell we should go to the next (previous) cell
        elif key == wx.WXK_DOWN:
            curline = self.LineFromPosition(self.GetCurrentPos())
            linecnt = self.GetLineCount()
            if curline == linecnt - 1: #Go to the next cell
                next = self.parent.GetNext(id = self.id)
                if next is None:
                    event.Skip()
                else:
                    pos = self.GetCurrentPos() - self.PositionFromLine(curline)
                    next.SetTheFocus(pos, start = True)
            else:
                event.Skip()
        elif key == wx.WXK_UP:
            curline = self.LineFromPosition(self.GetCurrentPos())
            #linecnt = self.GetLineCount()
            if curline == 0: #Go to the next cell
                prev = self.parent.GetPrev(id = self.id)
                if prev is None:
                    event.Skip()
                else:    
                    pos = self.GetCurrentPos() - self.PositionFromLine(curline)
                    prev.SetTheFocus(pos, start = False)
            else:
                event.Skip()
        elif key in NAVKEYS:
            event.Skip()
        # Protect the readonly portion of the shell.
        elif not self.CanEdit():
            pass
        else:
            event.Skip()
            
    def getLineStart(self):
        """returns the start position and the prompt
        lenght of the current line. Used when handling WX_HOME"""
        linenum = self.LineFromPosition(self.GetCurrentPos())
        promptlen = self.view.PromptLen(linenum)
        startpos = self.PositionFromLine(linenum)
        return (startpos, promptlen)

    def clearCommand(self):
        """Delete the current, unexecuted command."""
        startpos = self.promptPosEnd
        endpos = self.GetTextLength()
        self.SetSelection(startpos, endpos)
        self.ReplaceSelection('')
        self.more = False

    def OnHistoryReplace(self, step):
        """Replace with the previous/next command from the history buffer."""
        self.clearCommand()
        self.replaceFromHistory(step)

    def replaceFromHistory(self, step):
        """Replace selection with command from the history buffer."""
        ps2 = str(sys.ps2)
        self.ReplaceSelection('')
        newindex = self.historyIndex + step
        if -1 <= newindex <= len(self.history):
            self.historyIndex = newindex
        if 0 <= newindex <= len(self.history)-1:
            command = self.history[self.historyIndex]
            command = command.replace('\n', os.linesep + ps2)
            self.ReplaceSelection(command)

    def OnHistoryInsert(self, step):
        """Insert the previous/next command from the history buffer."""
        if not self.CanEdit():
            return
        startpos = self.GetCurrentPos()
        self.replaceFromHistory(step)
        endpos = self.GetCurrentPos()
        self.SetSelection(endpos, startpos)

    def OnHistorySearch(self):
        """Search up the history buffer for the text in front of the cursor."""
        if not self.CanEdit():
            return
        startpos = self.GetCurrentPos()
        # The text up to the cursor is what we search for.
        numCharsAfterCursor = self.GetTextLength() - startpos
        searchText = self.getCommand(rstrip=False)
        if numCharsAfterCursor > 0:
            searchText = searchText[:-numCharsAfterCursor]
        if not searchText:
            return
        # Search upwards from the current history position and loop
        # back to the beginning if we don't find anything.
        if (self.historyIndex <= -1) \
        or (self.historyIndex >= len(self.history)-2):
            searchOrder = range(len(self.history))
        else:
            searchOrder = range(self.historyIndex+1, len(self.history)) + \
                          range(self.historyIndex)
        for i in searchOrder:
            command = self.history[i]
            if command[:len(searchText)] == searchText:
                # Replace the current selection with the one we found.
                self.ReplaceSelection(command[len(searchText):])
                endpos = self.GetCurrentPos()
                self.SetSelection(endpos, startpos)
                # We've now warped into middle of the history.
                self.historyIndex = i
                break

    def setStatusText(self, text):
        """Display status information."""

        # This method will likely be replaced by the enclosing app to
        # do something more interesting, like write to a status bar.
        print text



    def getMultilineCommand(self, rstrip=True):
        """Extract a multi-line command from the editor.

        The command may not necessarily be valid Python syntax."""
        # XXX Need to extract real prompts here. Need to keep track of
        # the prompt every time a command is issued.
        ps1 = str(sys.ps1)
        ps1size = len(ps1)
        ps2 = str(sys.ps2)
        ps2size = len(ps2)
        # This is a total hack job, but it works.
        text = self.GetCurLine()[0]
        line = self.GetCurrentLine()
        while text[:ps2size] == ps2 and line > 0:
            line -= 1
            self.GotoLine(line)
            text = self.GetCurLine()[0]
        if text[:ps1size] == ps1:
            line = self.GetCurrentLine()
            self.GotoLine(line)
            startpos = self.GetCurrentPos() + ps1size
            line += 1
            self.GotoLine(line)
            while self.GetCurLine()[0][:ps2size] == ps2:
                line += 1
                self.GotoLine(line)
            stoppos = self.GetCurrentPos()
            command = self.GetTextRange(startpos, stoppos)
            command = command.replace(os.linesep + ps2, '\n')
            command = command.rstrip()
            command = command.replace('\n', os.linesep + ps2)
        else:
            command = ''
        if rstrip:
            command = command.rstrip()
        return command

    def getCommand(self, text=None, rstrip=True):
        """Extract a command from text which may include a shell prompt.

        The command may not necessarily be valid Python syntax."""
        if not text:
            text = self.GetCurLine()[0]
        # Strip the prompt off the front leaving just the command.
        command = self.lstripPrompt(text)
        if command == text:
            command = ''  # Real commands have prompts.
        if rstrip:
            command = command.rstrip()
        return command

    def lstripPrompt(self, text):
        """Return text without a leading prompt."""
        ps1 = str(sys.ps1)
        ps1size = len(ps1)
        ps2 = str(sys.ps2)
        ps2size = len(ps2)
        # Strip the prompt off the front of text.
        if text[:ps1size] == ps1:
            text = text[ps1size:]
        elif text[:ps2size] == ps2:
            text = text[ps2size:]
        return text

    def push(self, command):
        """Send command to the interpreter for execution."""
        self.write(os.linesep)
        busy = wx.BusyCursor()
        self.waiting = True
        self.more = self.interp.push(command)
        self.waiting = False
        del busy
        if not self.more:
            self.addHistory(command.rstrip())
        self.prompt()

    def addHistory(self, command):
        """Add command to the command history."""
        # Reset the history position.
        self.historyIndex = -1
        # Insert this command into the history, unless it's a blank
        # line or the same as the last command.
        if command != '' \
        and (len(self.history) == 0 or command != self.history[0]):
            self.history.insert(0, command)

    def write(self, text):
        """Display text in the shell.

        Replace line endings with OS-specific endings."""
        text = self.fixLineEndings(text)
        self.AddText(text)
        self.EnsureCaretVisible()

    def fixLineEndings(self, text):
        """Return text with line endings replaced by OS-specific endings."""
        lines = text.split('\r\n')
        for l in range(len(lines)):
            chunks = lines[l].split('\r')
            for c in range(len(chunks)):
                chunks[c] = os.linesep.join(chunks[c].split('\n'))
            lines[l] = os.linesep.join(chunks)
        text = os.linesep.join(lines)
        return text

    def prompt(self):
        """Display proper prompt for the context: ps1, ps2 or ps3.

        If this is a continuation line, autoindent as necessary."""
        isreading = self.reader.isreading
        skip = False
        if isreading:
            prompt = str(sys.ps3)
        elif self.more:
            prompt = str(sys.ps2)
        else:
            prompt = str(sys.ps1)
        pos = self.GetCurLine()[1]
        if pos > 0:
            if isreading:
                skip = True
            else:
                self.write(os.linesep)
        if not self.more:
            self.promptPosStart = self.GetCurrentPos()
        if not skip:
            self.write(prompt)
        if not self.more:
            self.promptPosEnd = self.GetCurrentPos()
            # Keep the undo feature from undoing previous responses.
            self.EmptyUndoBuffer()
        # XXX Add some autoindent magic here if more.
        if self.more:
            self.write(' '*4)  # Temporary hack indentation.
        self.EnsureCaretVisible()
        self.ScrollToColumn(0)

    def readline(self):
        """Replacement for stdin.readline()."""
        input = ''
        reader = self.reader
        reader.isreading = True
        self.prompt()
        try:
            while not reader.input:
                wx.YieldIfNeeded()
            input = reader.input
        finally:
            reader.input = ''
            reader.isreading = False
        input = str(input)  # In case of Unicode.
        return input

    def readlines(self):
        """Replacement for stdin.readlines()."""
        lines = []
        while lines[-1:] != ['\n']:
            lines.append(self.readline())
        return lines

    def raw_input(self, prompt=''):
        """Return string based on user input."""
        if prompt:
            self.write(prompt)
        return self.readline()

    def ask(self, prompt='Please enter your response:'):
        """Get response from the user using a dialog box."""
        dialog = wx.TextEntryDialog(None, prompt,
                                    'Input Dialog (Raw)', '')
        try:
            if dialog.ShowModal() == wx.ID_OK:
                text = dialog.GetValue()
                return text
        finally:
            dialog.Destroy()
        return ''

    def pause(self):
        """Halt execution pending a response from the user."""
        self.ask('Press enter to continue:')

    def clear(self):
        """Delete all text from the shell."""
        self.ClearAll()

    def run(self, command, prompt=True, verbose=True):
        """Execute command as if it was typed in directly.
        >>> shell.run('print "this"')
        >>> print "this"
        this
        >>>
        """
        # Go to the very bottom of the text.
        endpos = self.GetTextLength()
        self.SetCurrentPos(endpos)
        command = command.rstrip()
        if prompt: self.prompt()
        if verbose: self.write(command)
        self.push(command)

    def runfile(self, filename):
        """Execute all commands in file as if they were typed into the
        shell."""
        file = open(filename)
        try:
            self.prompt()
            for command in file.readlines():
                if command[:6] == 'shell.':
                    # Run shell methods silently.
                    self.run(command, prompt=False, verbose=False)
                else:
                    self.run(command, prompt=False, verbose=True)
        finally:
            file.close()

    def autoCompleteShow(self, command):
        """Display auto-completion popup list."""
        list = self.log.interp.getAutoCompleteList(command,
                    includeMagic=self.autoCompleteIncludeMagic,
                    includeSingle=self.autoCompleteIncludeSingle,
                    includeDouble=self.autoCompleteIncludeDouble)
        if list:
            options = ' '.join(list)
            offset = 0
            self.AutoCompShow(offset, options)

    def autoCallTipShow(self, command):
        """Display argument spec and docstring in a popup window."""
        if self.CallTipActive():
            self.CallTipCancel()
        (name, argspec, tip) = self.interp.getCallTip(command)
        if tip:
            dispatcher.send(signal='Shell.calltip', sender=self, calltip=tip)
        if not self.autoCallTip:
            return
        if argspec:
            startpos = self.GetCurrentPos()
            self.write(argspec + ')')
            endpos = self.GetCurrentPos()
            self.SetSelection(endpos, startpos)
        if tip:
            curpos = self.GetCurrentPos()
            tippos = curpos - (len(name) + 1)
            fallback = curpos - self.GetColumn(curpos)
            # In case there isn't enough room, only go back to the
            # fallback.
            tippos = max(tippos, fallback)
            self.CallTipShow(tippos, tip)

    def writeOut(self, text):
        """Replacement for stdout."""
        self.write(text)

    def writeErr(self, text):
        """Replacement for stderr."""
        self.write(text)

    def redirectStdin(self, redirect=True):
        """If redirect is true then sys.stdin will come from the shell."""
        if redirect:
            sys.stdin = self.reader
        else:
            sys.stdin = self.stdin

    def redirectStdout(self, redirect=True):
        """If redirect is true then sys.stdout will go to the shell."""
        if redirect:
            sys.stdout = PseudoFileOut(self.writeOut)
        else:
            sys.stdout = self.stdout

    def redirectStderr(self, redirect=True):
        """If redirect is true then sys.stderr will go to the shell."""
        if redirect:
            sys.stderr = PseudoFileErr(self.writeErr)
        else:
            sys.stderr = self.stderr

    def CanCut(self):
        """Return true if text is selected and can be cut."""
        if self.GetSelectionStart() != self.GetSelectionEnd() \
               and self.GetSelectionStart() >= self.promptPosEnd \
               and self.GetSelectionEnd() >= self.promptPosEnd:
            return True
        else:
            return False

    def CanPaste(self):
        """Return true if a paste should succeed."""
        if self.CanEdit() and editwindow.EditWindow.CanPaste(self):
            return True
        else:
            return False


    def CanEdit(self, oper = 'insert'):
        """Return true if the given editing operation should succeed. oper can
        be one of: 'insert', 'delete', and 'backspace'"""
        #TODO: why we need to know anythong about the selection here
        #if self.GetSelectionStart() != self.GetSelectionEnd():
        #    if self.GetSelectionStart() >= self.promptPosEnd \
        #           and self.GetSelectionEnd() >= self.promptPosEnd:
        #        return True
        #    else:
        #        return False
        #else:
        #    return self.GetCurrentPos() >= self.promptPosEnd
        
        pos = self.GetCurrentPos()
        line = self.LineFromPosition(pos)
        
        i = 1
        if oper == 'insert':
            i = 0
        elif oper == 'delete':
            #Delete is the same as backspace on the next character
            nextpos = pos +1
            nextline = self.PositionFromLine(nextpos)
            if nextline > line:
                nextpos += self.view.Promptlen(nextline)
                pos = nextpos
                line = nextline

        if not self.view.CanEdit(line):
            return False
        
        #Check if the cursor is inside the prompt
        startpos = self.PositionFromLine(line)
        promptlen = self.view.PromptLen(line)
        
        if startpos+promptlen + i > pos:
            return False
        else:
            return True

    def Cut(self):
        """Remove selection and place it on the clipboard."""
        if self.CanCut() and self.CanCopy():
            if self.AutoCompActive():
                self.AutoCompCancel()
            if self.CallTipActive():
                self.CallTipCancel()
            self.Copy()
            self.ReplaceSelection('')

    def Copy(self):
        """Copy selection and place it on the clipboard."""
        if self.CanCopy():
            #ps1 = str(sys.ps1)
            #ps2 = str(sys.ps2)
            command = self.GetSelectedText()
            #command = command.replace(os.linesep + ps2, os.linesep)
            #command = command.replace(os.linesep + ps1, os.linesep)
            #command = self.lstripPrompt(text=command)
            data = wx.TextDataObject(command)
            self._clip(data)

    def CopyWithPrompts(self):
        """Copy selection, including prompts, and place it on the clipboard."""
        if self.CanCopy():
            command = self.GetSelectedText()
            data = wx.TextDataObject(command)
            self._clip(data)

    def CopyWithPromptsPrefixed(self):
        """Copy selection, including prompts prefixed with four
        spaces, and place it on the clipboard."""
        if self.CanCopy():
            command = self.GetSelectedText()
            spaces = ' ' * 4
            command = spaces + command.replace(os.linesep,
                                               os.linesep + spaces)
            data = wx.TextDataObject(command)
            self._clip(data)

    def _clip(self, data):
        if wx.TheClipboard.Open():
            wx.TheClipboard.UsePrimarySelection(False)
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Flush()
            wx.TheClipboard.Close()

    def Paste(self):
        """Replace selection with clipboard contents."""
        if self.CanPaste() and wx.TheClipboard.Open():
            ps2 = str(sys.ps2)
            if wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_TEXT)):
                data = wx.TextDataObject()
                if wx.TheClipboard.GetData(data):
                    self.ReplaceSelection('')
                    command = data.GetText()
                    command = command.rstrip()
                    command = self.fixLineEndings(command)
                    command = self.lstripPrompt(text=command)
                    command = command.replace(os.linesep + ps2, '\n')
                    command = command.replace(os.linesep, '\n')
                    command = command.replace('\n', os.linesep + ps2)
                    self.write(command)
            wx.TheClipboard.Close()

    def PasteAndRun(self):
        """Replace selection with clipboard contents, run commands."""
        if wx.TheClipboard.Open():
            ps1 = str(sys.ps1)
            ps2 = str(sys.ps2)
            if wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_TEXT)):
                data = wx.TextDataObject()
                if wx.TheClipboard.GetData(data):
                    endpos = self.GetTextLength()
                    self.SetCurrentPos(endpos)
                    startpos = self.promptPosEnd
                    self.SetSelection(startpos, endpos)
                    self.ReplaceSelection('')
                    text = data.GetText()
                    text = text.lstrip()
                    text = self.fixLineEndings(text)
                    text = self.lstripPrompt(text)
                    text = text.replace(os.linesep + ps1, '\n')
                    text = text.replace(os.linesep + ps2, '\n')
                    text = text.replace(os.linesep, '\n')
                    lines = text.split('\n')
                    commands = []
                    command = ''
                    for line in lines:
                        if line.strip() == ps2.strip():
                            # If we are pasting from something like a
                            # web page that drops the trailing space
                            # from the ps2 prompt of a blank line.
                            line = ''
                        if line.strip() != '' and line.lstrip() == line:
                            # New command.
                            if command:
                                # Add the previous command to the list.
                                commands.append(command)
                            # Start a new command, which may be multiline.
                            command = line
                        else:
                            # Multiline command. Add to the command.
                            command += '\n'
                            command += line
                    commands.append(command)
                    for command in commands:
                        command = command.replace('\n', os.linesep + ps2)
                        self.write(command)
                        self.processLine()
            wx.TheClipboard.Close()

    def wrap(self, wrap=True):
        """Sets whether text is word wrapped."""
        try:
            self.SetWrapMode(wrap)
        except AttributeError:
            return 'Wrapping is not available in this version.'

    def zoom(self, points=0):
        """Set the zoom level.

        This number of points is added to the size of all fonts.  It
        may be positive to magnify or negative to reduce."""
        self.SetZoom(points)
