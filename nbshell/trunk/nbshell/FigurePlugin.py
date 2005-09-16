"""FigurePlugin.py Contains classes needed to display figures"""

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

import os.path

import wx

from lxml import etree

from nbshell.ipnNotebookWidget import CellCtrlBase

def GetPluginFactory():
    """ Returns the factory object for the plugin. This function is called
    at the start of the program and should be called only once.
    """
    return FigurePluginFactory()

class FigurePluginFactory(object):
    string = "figure"
    type = "encoded"
        
    def CreateDocumentPlugin(self,document, element):
        """Creates the document part of the plugin. The returned object is 
        stored in ipgDocument.celllist. element is an <ipython-figure> element
        """
        return FigureDocumentPlugin(document, element)
    
    def CreateViewPlugin(self,docplugin, view):
        """ Creates a view plugin connected to the given document plugin and 
        the given view. The view plugin is responsible for creating windows,
        handling events, etc. In simple plugins the document and the view plugin
        may be the same object
        """
        
        if view.type=="notebook":
            return FigureNotebookViewPlugin(docplugin, view)
        else:
            return None #Well here I should throw an exception, however I am 
                        #not supposed to get to this line for a long long time
    
    def get_matchers(self):
        """A matcher for the <ipython-figure> element"""
        return lambda element:element.tag == 'ipython-figure'
        

#end GenericPluginFactory

class FigureDocumentPlugin(object):
    """ objects of this class are responsible for storing data, serializing and
    loding data, and updating the view plugins"""
    def __init__(self, document, element):
        """Initialization"""
        self.document = document
        self.sheet = self.document.sheet
        self.view = None    #This plugin is designed for a single view. For
                            #multiple view there should be some modifications
        self.element = element #This stores the <ipython-figure> element

    type = 'figure'

    def get_xml_text(self):
        return etree.tostring(self.element, encoding = 'utf-8')

    def __len__(self):
        return 1
    
    def Split(self, pos):
        assert(0)
        
    def Concat(self, block, update = True):
        """See PythonDocumentPlugin.Concat"""
        return False

    def Clear(self):
        """Clears all data"""
        return

    def GetFactory(self):
        """Returns a factory instance"""
        return GenericPluginFactory()
    
    def SetSavePoint(self):
        pass
    def IsModified(self):
        return False
    modified = property(fget = IsModified)

class FigureNotebookViewPlugin(object):
    """A generic view plugin. Used for handling data display."""
    def __init__(self, docplugin, view):
        """ Initialization"""
        self.view = view
        self.doc = docplugin
        self.doc.view = self
        self.document=docplugin.document
        self.sheet = self.doc.sheet
        self.window = None
        self.image = None   #a wx.Image object, storing the image
        #wx.Image.InsertHandler(wx.PNGHandler)
        self.bitmap = None

    def SetFocus(self):
        if self.window is not None:
            self.window.SetFocus()

    def __set_focus(self,event):
        self.doc.sheet._currentcell = self.doc
        event.Skip()

    def createWindow(self):
        """Creates the widget for displaying the figure. Does nothing if it is
        already created"""
        if self.window is not None:
            return self.window
        #1. Create the window
        self.window = FigureCtrl(self.view, -1)
        wx.EVT_SET_FOCUS(self.window, self.__set_focus)
        wx.EVT_PAINT(self.window, self.OnPaint)
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
        return self.window
    
    def Update(self):
        """ This method is required for all view implementations. It must
        update the view."""

        if self.window is None:
            self.createWindow()
        
        #Create the image object
        #Get the image file for the 
        filename = os.path.expanduser(self.doc.element.attrib['filename'])
        #If this is not an absolute path, add fileinfo['path']
        if not os.path.isabs(filename):
            filename = self.document.fileinfo['path']+'/'+filename
        filename = os.path.normpath(filename)
        #TODO: Proper error handling
        self.image = wx.Image(filename)
        #Get a bitmap from the image
        self.bitmap = wx.BitmapFromImage(self.image)
        #Recalculate the window size
        self.window.SetClientSizeWH(self.image.GetWidth(),\
                                    self.image.GetHeight())
        #update the notebook view
        self.view.RelayoutCells(id = self.id)
        #Get the window DC and draw the image
        dc = wx.ClientDC(self.window)
        dc.BeginDrawing()
        dc.DrawBitmap(self.bitmap,0,0)
        dc.EndDrawing()
        
    def OnPaint(self, event):
        """Ratepaints the window"""
        if self.bitmap is not None:
            dc = wx.PaintDC(self.window)
            dc.BeginDrawing()
            dc.Clear()
            dc.DrawBitmap(self.bitmap,0,0)
            dc.EndDrawing()
            
    def GetFirstId(self):
        """ This view is responsible for a list of consequent windows in the
        #notebook widget. GetFirsId returns the id of the first window"""
        return self.id
        
    def GetLastId(self):
        """See the description of GetFirstId"""
        return self.id
    
    def UpdateDoc(self):
        """ This method updates data in the document, from the user input in
        the view """
        pass
    
    def Close(self, update=True):
        """ This method is called when the document cell is
        destroyed. It must close all windows. If update is false, do
        not update the view"""
        index = self.view.GetIndex(self.id)
        self.view.DeleteCell(index, update)
        
    position = property(fget = lambda :0, fset = lambda x:None)

class FigureCtrl(CellCtrlBase):
    """Window used for displaying a figure"""

    def __init__ (self, parent, id, pos = wx.DefaultPosition, size =
                  wx.DefaultSize, style=0, name="figure"):
        """ Standard __init__ function."""
        CellCtrlBase.__init__(self, parent, id, pos, size, style, name)