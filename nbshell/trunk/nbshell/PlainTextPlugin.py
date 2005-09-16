
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
from nbshell.ipnNotebookWidget import CellCtrlBase

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
        
    def CreateDocumentPlugin(self,document, text = None):
        """Creates the document part of the plugin. The returned object is 
        stored in ipgDocument.celllist and is responsible for storing and
        serialization of data. "data" contains initial data for the plugin.
        """
        return PlainTextDocumentPlugin(document, text)
    
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
    
    def get_matchers(self):
        """No matchers"""
        return None
#end GenericPluginFactory

class PlainTextDocumentPlugin(object):
    def __init__(self, document, text = None):
        """Initialization. If element is <sheet> then the text is
        element.text. If the element is something else, then the text is
        element.tail"""
        
        self.document = document
        self.sheet = document.sheet
        self._text = text or ''
        self.index = None   #Set by AddCell, InsertCell, DeleteCell
        self.view = None    #This plugin is designed for a single view. For
                            #multiple views there should be some modifications

    type='plaintext'
    
    def SetText(self, text):
        try:
            self.view.window.SetText(text)
        except:
            pass
        self._text = text
    
    def GetText(self):
        try:
            return self.view.window.GetText()
        except:
            return self._text

    text = property(fget = GetText,fset = SetText)
    
    def get_xml_text(self):
        """Return the xml text representing the document"""
        return self.text
    
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
        return self.view.window.GetLength()
    
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
        return lambda p:\
            self.sheet.InsertCell('plaintext', p, update = False, text = text[pos:])
    
    def Concat(self, block, update = True):
        """ Appends the data in the given text at the end of the this block
        """
        assert block.type == 'plaintext'
        self.text = self.text + block.text
        return True
        #update is automatic

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
            self.window.SetText(self.doc._text)
        #print 'text -> %s'%self.doc.text #dbg
        

    def UpdateDoc(self):
        """Update data in the document"""
        pass
        #self.doc.text = self.window.GetText()
        
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
        #self.doc.text = self.window.GetText()
        pos = self.window.GetCurrentPos()
        self.doc.sheet.InsertCode(self.doc,pos, update = True)
        

class PlainTextCtrl(stc.StyledTextCtrl, CellCtrlBase):

    """ PlainTextCtrl - the widget responsible for displaying and
    editing plain text. It has only basic functionality and can be
    used as a reference on how to make more complicated editing
    plugins.
    """

    def __init__ (self, parent, id, pos = wx.DefaultPosition, size = wx.DefaultSize, style=0, name="plaintext"):

        """ Standard __init__ function."""
        stc.StyledTextCtrl.__init__(self, parent, id, pos, size, style, name)
        CellCtrlBase.__init__(self,parent, id, pos, size, style, name)
        self.oldlineno = 1 # used by OnModified. Is there a way to
                           # declare this inside the method? Like a
                           # C++ static variable
        self.oldpos = (0,0)
        self.SetUseHorizontalScrollBar(0)
        self.SetLexer(stc.STC_LEX_XML)
        self.StyleSetSpec(stc.STC_H_TAG,"fore:#0000FF")
        self.StyleSetSpec(stc.STC_STYLE_LINENUMBER, "back:#E0C0C0")

        self.SetKeyWords(0,'para title section')
        
        stc.EVT_STC_MODIFIED(self, id, self.OnModified)
        stc.EVT_STC_UPDATEUI(self, id, self.OnUpdateUI)
        
        

    def _get_position(self):
        pos = self.GetCurrentPos()
        line = self.LineFromPosition(pos)
        return (pos, line , pos - self.PositionFromLine(line))
    
    def _get_length(self):
        pos = self.GetCurrentPos()
        line = self.LineFromPosition(pos)
        line_length = self.GetLineEndPosition(line) - self.PositionFromLine(line)
        return (self.GetLength(), self.GetLineCount(), line_length)
    
    position = property(_get_position)
    length = property(_get_length)
    
    def Resize (self, width = None):
        """ See CellCtrlBase.Resize """
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
        #self.view.doc.text = self.GetText()
        lineno = self.GetLineCount()
        if self.oldlineno != lineno :
            self.oldlineno = lineno
            self.parent.RelayoutCells(id = self.id)

    def OnUpdateUI (self, evt):
        pos = tuple(self.PointFromPosition(self.GetCurrentPos()))
        if (pos != self.oldpos):
            self.parent.ScrollTo(self.view.doc.index, pos) # show the highest pixel of the caret
            self.parent.ScrollTo(self.view.doc.index, (pos[0], pos[1]+self.TextHeight(0))) # now show the lowest pixel.
            #TODO: If there is a way to make scrolling slower, I can't
            #think of it right now :)
            self.oldpos = pos

    def OnKeyDown(self, evt):
        """ Called whenever a key is pressed. The keys which are not
        processed are skipped.
        """
        controlDown = evt.ControlDown()
        keycode = evt.GetKeyCode()
        if keycode in [ord('i'),ord('I')] and controlDown:
            #insert a code cell
            self.view.InsertCode()
        else:
            evt.Skip()
