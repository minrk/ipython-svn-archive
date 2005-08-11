
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

import StringIO

import wx
from wx import stc

from nbshell.SimpleXMLWriter import XMLWriter

def GetPluginFactory():
    """ Returns the factory object for the plugin. This function is called
    at the start of the program and should be called only once.
    """
    return PlainTextPluginFactory()

class PlainTextPluginFactory(object):
    """ This class is responsible for creating the document and view parts of 
    a plugin. Also it has some functions giving information about the plugin.
    The reason this class exists is because the document and view classes of
    the program shouldn't care how plugin objects are created. For example all
    the plain text in the notebook could be contained a single object which is 
    returned every time the document class wants to get a new one."""
    
    string = "plaintext"
    #def GetString(self):
    #    """ Returns the type string of the plugin. This is used when a notebook
    #    file is loaded. See notebookformat.txt for more info"""
    #    return "plaintext"
    
    type = "encoded"
    #def GetType(self):
    #    """ Returns the way data should be passed to the plugin. Currently
    #    supported types are "raw" and "encoded". See notebookformat.txt for 
    #    more info"""
    #    return "encoded" #Probably only the python code plugin should be raw
        
    def CreateDocumentPlugin(self,document):
        """Creates the document part of the plugin. The returned object is 
        stored in ipgDocument.celllist and is responsible for storing and
        serialization of data. "data" contains initial data for the plugin.
        """
        return PlainTextDocumentPlugin(document)
    
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
            return PlainTextNotebookViewPlugin(docplugin, view)
        else:
            return None #Well here I should throw an exception, however I am 
                        #not supposed to get to this line for a long long time
#end GenericPluginFactory

class PlainTextDocumentPlugin(object):
    def __init__(self, document):
        """Initialization. If element is <sheet> then the text is
        element.text. If the element is something else, then the text is
        element.tail"""
        
        self.document = document
        self.sheet = document.sheet
        self.text = ''
        self.index = None   #Set by AddCell, InsertCell, DeleteCell
        self.view = None    #This plugin is designed for a single view. For
                            #multiple views there should be some modifications

    type='plaintext'
    
    def LoadXML(self, iterator, prevlist, elemlist, endtaglist):
        """The LoadXML method gets text representing a part of the xml tree.
        The first element in this part is 'elemlist[-1]', the next are
        retrieved by 'iterator'. 'prevlist' and 'elemlist' are the previous two
        results of calling 'iterator.next()'. The LoadXML method stops when the
        'iterator' throws a 'StopIteration' exception, or it finds an element for
        which there is a plugin to process it. Currently there are such
        plugins for the <ipython-block> and <ipython-figure> elements. In that
        case it returns the last 'elemlist'. The tags on which LoadXML
        should exit are in 'endtaglist'"""
        
        text = StringIO.StringIO()
        #TODO: what encoding should I choose?
        writer = XMLWriter(text, encoding='utf-8')

        l1 = len(prevlist)
        i = l1-1
        l2 = len(elemlist)
        while i>=0 and (i>= l2 or prevlist[i] != elemlist[i]):
            writer.end(prevlist[i].tag)
            writer.data(prevlist[i].tail or '')
            i-=1

        while elemlist != () and elemlist[-1].tag not in endtaglist:
            prevlist = elemlist
            writer.start(elemlist[-1].tag, elemlist[-1].attrib)
            writer.data(elemlist[-1].text or '')
            try:
                elemlist = iterator.next()
            except StopIteration:
                elemlist = ()
            l1 = len(prevlist)
            i = l1-1
            l2 = len(elemlist)
            while i>=0 and (i>= l2 or prevlist[i] != elemlist[i]):
                writer.end(prevlist[i].tag)
                writer.data(prevlist[i].tail or '')
                i-=1
            
        writer.flush()
        self.text = text.getvalue()
        if elemlist == ():
            raise StopIteration
        else: #elemlist[-1].tag in endtaglist:
            return elemlist
        
        
    def __len__(self):
        return self.view.window.GetLenght()
    
    def SetSavePoint(self):
        self.view.SetSavePoint()
    def IsModified(self):
        return self.view.modified
    modified = property(fget = IsModified)

    #def GetText(self):
    #    text = self.element.text
    #    if self.start:
    #        text = self.element.text
    #    else:
    #        text = self.element.tail
    #    return (text is not None) and text or ''

    #def SetText(self, text):
    #    """Sets the text in the document"""
    #    if self.start:
    #        self.element.text = text
    #    else:
    #        self.element.tail = text
    #    return text
    
    def Clear(self):
        """Clears all data"""
        self.text = ''
        if self.view is not None:
            self.view.Update()

    #text = property(GetText, SetText, Clear, doc = """The text contained in this instance""")
    
    def GetFactory(self):
        return PlainTextPluginFactory()
    
    def Split(self, pos, update = True):
        """Removes the text after the given position and returns it"""
        text = self.text
        self.text = text[:pos]
        if update:
            self.view.Update()
        return text[pos:]

class PlainTextNotebookViewPlugin(object):
    def __init__(self, docplugin, view):
        """Initialization"""
        self.view = view
        self.doc = docplugin
        self.doc.view = self
        self.window = None
        #self.document = docplugin.document
        self.sheet = docplugin.sheet
        
    def SetFocus(self):
        if self.window is not None:
            self.window.SetFocus()
            
    #self.position is a property which can get and set the current position in
    #the cell. It behaves differently in different types of cells
    def __get_position(self):
        if self.window is None:
            return 0
        else:
            return self.window.GetCurrentPos()

    def __set_position(self, pos):
        if self.window is not None:
            self.window.SetCurrentPos(pos)
    position = property(fget = __get_position, fset = __set_position)

    def GetFirstId(self):
        """ This view is responsible for a list of consequent windows in the
        #notebook widget. GetFirsId returns the id of the first window"""
        return self.id
        
    def GetLastId(self):
        """See the description of GetFirstId"""
        return self.id

    def __set_focus(self,event):
        self.doc.sheet._currentcell = self.doc
        event.Skip()
        
    def createWindow(self):
        """Creates the window. If it is already created returns it"""
        if self.window is None: #create the window
            #1. Create the window and set the document plugin
            self.window = PlainTextCtrl(self.view, -1)
            wx.EVT_SET_FOCUS(self.window, self.__set_focus)
            self.id = self.window.GetId()
            #print "id:", self.id #dbg
            self.window.view = self
            #2. Add the window at the correct place in the notebook widget
            if self.doc.index == 0: #put the window at the beginning of the document
                self.view.InsertCell(self.window, 0, update=False)
            else:
                prevcell = self.sheet.GetCell(self.doc.index-1)
                viewplugin = prevcell.view
                #print self.doc.index #dbg
                #print viewplugin #dbg
                lastid = viewplugin.GetLastId()
                #print lastid #dbg
                index = self.view.GetIndex(lastid)+1
                self.view.InsertCell(self.window, index, update = False)
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
        #print 'text -> %s'%self.doc.text #dbg
        self.window.SetText(self.doc.text)

    def UpdateDoc(self):
        """Update data in the document"""
        self.doc.text = self.window.GetText()
        
    def SetSavePoint(self):
        if self.window is not None:
            self.window.SetSavePoint()
    
    def IsModified(self):
        if self.window is not None:
            return self.window.GetModify()
        else:
            return False
    modified = property(fget = IsModified)
        
    def Close(self, update = True):
        index = self.view.GetIndex(self.id)
        self.view.DeleteCell(index, update)
    
    def InsertCode(self):
        #lazy document update. We update the document when it is needed
        self.doc.text = self.window.GetText()
        pos = self.window.GetCurrentPos()
        self.doc.sheet.InsertCode(self.doc,pos, update = True)
        

class PlainTextCtrl(stc.StyledTextCtrl):

    """ PlainTextCtrl - the widget responsible for displaying and
    editing plain text. It has only basic functionality and can be
    used as a reference on how to make more complicated editing
    plugins.
    """

    def __init__ (self, parent, id, pos = wx.DefaultPosition, size = wx.DefaultSize, style=0, name="plaintext"):

        """ Standard __init__ function."""

        stc.StyledTextCtrl.__init__(self, parent, id, pos, size, style, name)
        self.id = self.GetId()
        self.parent = parent
        self.oldlineno = 1 # used by OnModified. Is there a way to
                           # declare this inside the method? Like a
                           # C++ static variable
        self.oldpos = (0,0)
        self.SetUseHorizontalScrollBar(0)
        stc.EVT_STC_MODIFIED(self, id, self.OnModified)
        stc.EVT_STC_UPDATEUI(self, id, self.OnUpdateUI)
        wx.EVT_KEY_DOWN(self, self.OnKeyDown)

        
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
        #TODO: This might be slow
        self.view.doc.text = self.GetText()
        lineno = self.GetLineCount()
        if self.oldlineno != lineno :
            self.oldlineno = lineno
            self.parent.RelayoutCells(id = self.id)

    def OnUpdateUI (self, evt):
        pos = tuple(self.PointFromPosition(self.GetCurrentPos()))
        if (pos != self.oldpos):
            self.parent.ScrollTo(self.view.doc.index, pos) # show the highest pixel of the caret
#            self.view.ScrollTo(self.cell.index, (pos[0], pos[1]+self.TextHeight(0))) # now show the lowest pixel.
            #TODO: If there is a way to make scrolling slower, I can't
            #think of it right now :)
            self.oldpos = pos

    def OnKeyDown(self, evt):
        """ Called whenever a key is pressed. The keys which are not
        processed are skipped.
        """
        controlDown = evt.ControlDown()
        keycode = evt.GetKeyCode()
        if keycode == wx.WXK_DOWN: 
            curline = self.LineFromPosition(self.GetCurrentPos())
            linecount = self.GetLineCount()
            if curline == linecount - 1: #Go to the next cell
                next = self.parent.GetNext(id = self.id)
                if next is None:
                    evt.Skip()
                else:
                    pos = self.GetCurrentPos() - self.PositionFromLine(curline)
                    next.SetTheFocus(pos, start = True)
            else:
                evt.Skip()
        elif keycode == wx.WXK_UP:
            curline = self.LineFromPosition(self.GetCurrentPos())
            linecount = self.GetLineCount()
            if curline == 0: #Go to the next cell
                prev = self.parent.GetPrev(id = self.id)
                if prev is None:
                    evt.Skip()
                else:    
                    pos = self.GetCurrentPos() - self.PositionFromLine(curline)
                    prev.SetTheFocus(pos, start = False)
            else:
                evt.Skip()
        elif keycode in [ord('i'),ord('I')] and controlDown:
            #insert a code cell
            self.view.InsertCode()
        else:
            evt.Skip()
