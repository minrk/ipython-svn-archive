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


import wx

class CellCtrlBase(wx.Window):
    """ A widget having all basic functionality for a cell. All other widgets
    should derive from this one"""
    

    def __init__ (self, parent, id, pos = wx.DefaultPosition, size =
                  wx.DefaultSize, style=0, name=''):
        """ Initialize the control."""
        
        #Check if the window is already created. If so don't create it again
        try:
            self.Enable()
        except:
            wx.Window.__init__(self, parent, id, pos, size, style, name)
        self.id = self.GetId()
        self.parent = parent
        wx.EVT_KEY_DOWN(self, lambda evt:CellCtrlBase.KeyDown(self,evt))

    #Overwrite the following properties to match the desired behaviour in the
    #control
    
    position = property(lambda self:(0,0,0), doc = 
        """ Returns a tuple describing the current position. The tuple has
        format (pos,line,pos_in_line) where pos is the current position in the
        control, line is the current line number and pos_in_line is the
        position in the current line of the cursor. The default implementation
        always returns (0,0,0)""")
    
    length = property(lambda self:(1,1,1), doc = 
        """ Returns a tuple of the form (length, number_of_lines,
        length_of_current_line) describing the length of the control. The
        default implementation returns (1,1,1)""")

    def Resize (self, width = None):
        """ Called when the width of the window needs to be resized. It is
        used for widgets to resize the height accordingly"""
        return #The default implementation does nothing

    def SetTheFocus(self, pos, start):
        """ Sets the focus to this cell """
        self.SetFocus()
    
    def KeyDown(self, evt):
        """ Called whenever a key is pressed. If a key is not processed in the
        method, calls self.OnKeyDown with the given event as a parameter. So
        if you want to add more key bindings overwrite the OnKeyDown method"""
        keycode = evt.GetKeyCode()
        #Get the values of the properties here, because I'll use them many
        #times
        position = self.position
        length = self.length
        if keycode == wx.WXK_DOWN: 
            if position[1] == length[1] -1: #this is the last line
                next = self.parent.GetNext(id = self.id)
                if next is None:
                    self.OnKeyDown(evt)
                else:
                    next.SetTheFocus(position[2], start = True)
            else:
                self.OnKeyDown(evt)
        elif keycode == wx.WXK_UP:
            if position[1] == 0: #Go to the previous
                prev = self.parent.GetPrev(id = self.id)
                if prev is None:
                    self.OnKeyDown(evt)
                else:    
                    prev.SetTheFocus(position[2], start = False)
            else:
                self.OnKeyDown(evt)
        else:
            self.OnKeyDown(evt)
            
    def OnKeyDown(self,evt):
        evt.Skip()

class ipnNotebook (wx.ScrolledWindow):
    """
    A widget having the base functionality of a Mathematica and Maple
    - like notebook. It holds cells with various types of
    information. Each cell is responsible for painting itself and
    handling user input. The cells can only be ordered vertically, you
    cannot have cells next to each other. 

    """

    def __init__ (self, parent, id=-1, pos=wx.DefaultPosition,
                  size=wx.DefaultSize, style=wx.VSCROLL|wx.HSCROLL,
                  validator=wx.DefaultValidator, name="NotebookWidget"):
        """ Initialize """

        
        wx.ScrolledWindow.__init__(self, parent, id, pos, size, style, name)
        self.type = "notebook"
        self.celllist = []
        self.id_dict = {-1:-1} #dictionary giving indeces corresponding to window ids
        self.activecell = -1
        self.vscrollstep = 17
        self.hscrollstep = 8
#        self.vscrollpos = 0
#        self.hscrollpos = 0
        self.vsize = 0
        self.hsize = 2000 # TODO: This must not be set explicitly
        self.AdjustScrollbars()
        self.SetBackgroundColour(wx.WHITE)
        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_MOUSEWHEEL(self, self.OnWheel)

    def OnWheel(self, evt):
        """Processes the mouse wheel events"""
        pos = self.GetScrollPos(wx.VERTICAL)
        self.Scroll(-1, max((pos - evt.m_wheelRotation/evt.m_wheelDelta*evt.m_linesPerAction,0)))

    def AdjustScrollbars(self, vpos = -1, hpos = -1):
        self.SetVirtualSize((self.hsize, self.vsize))
        self.SetScrollRate(self.hscrollstep, self.vscrollstep)


    def OnSize (self, event):
        self.AdjustScrollbars()
        
    def _getsumheights (self, index):
        """ Gets the sum of heights of the cells with indexes less
        than index
        """
        return  sum([self.celllist[i].GetSizeTuple()[1] for i in range(index)], 0)
        
    def Update(self, plugins = False):
        """Updates the view. Does not call the Update methods of the view
        plugins"""
        self.RelayoutCells(index=0)
    
    def RelayoutCells(self, index=None, id = None):
        """Layouts the cells self.celllist[index:] If id is given instead of
         then get the corresponding index"""
        if index is None:
            index = self.id_dict[id]
        sum_height = self._getsumheights(index)
        viewStart = self.GetViewStart()
#       print viewStart
        for cell in self.celllist[index:]:
            cell.Resize(self.hsize) # resize the cell if needed. See
                                    # StatixTextPlugin on possible ways to
                                    # implement this method
            cell_height = cell.GetSizeTuple()[1]
            height = sum_height + cell_height
            
            cell.SetDimensions(0-viewStart[0]*self.hscrollstep, sum_height-viewStart[1]*self.vscrollstep, self.hsize, cell_height)
            sum_height = height
        self.vsize = sum_height
        self.AdjustScrollbars()        

    def ScrollTo(self, index, pos):
        """Scrolls the window to make the point at pos visible. Pos is
        given in pixels. The position is relative to the start of the
        cell with the given index. When pos is visible, does
        nothing. When the current position at the active cell changes
        the plugin should call ScrollTo with the new position in order
        to update the UI.
        """
        cellStart = self._getsumheights(index) # This function is called
                                          # too often. TODO: Maybe I
                                          # should keep the window
                                          # positions in a list?
        virtPosPixel = (pos[0],cellStart+pos[1]) # the position in pixels
        
        virtPosScroll = (virtPosPixel[0]/self.hscrollstep, virtPosPixel[1]/self.vscrollstep) # the position in scroll units
        viewStart = self.GetViewStart()
        wndSize = self.GetClientSize()
        viewEnd = (viewStart[0]+wndSize[0]/self.hscrollstep, viewStart[1]+wndSize[1]/self.vscrollstep)
        (x, y) = viewStart #where to scroll
#        print x,y, "<- view start"
        if virtPosScroll[0]<viewStart[0]:
            x = virtPosScroll[0]
        elif virtPosScroll[0]>=viewEnd[0]:
                x = viewStart[0] + 1+ virtPosScroll[0] - viewEnd[0]

        if virtPosScroll[1]<viewStart[1]:
            y = virtPosScroll[1]
        elif virtPosScroll[1]>=viewEnd[1]:
                y = viewStart[1] + 1+ virtPosScroll[1] - viewEnd[1]
#        print x,y, "<- scroll to"
        if (x,y) != viewStart :
            self.Scroll(x,y)

       
    def AddCell (self, cell, update =True):
        """ Adds a cell to the celllist. The cell is added to the end
        of the list. If update is False, RelayoutCells is not called. This 
        is done, so if you need to add or delete more than one cell you will only
        need to call RelayoutCells once, via self.Update"""

        #Add the needed event handlers
        wx.EVT_MOUSEWHEEL(cell, self.OnWheel)

        self.celllist.append(cell);
        index = len(self.celllist) - 1
        if update: 
            self.RelayoutCells(index)
        self.id_dict[cell.GetId] = index
        return index
            
    def InsertCell(self, cell, index, update = True):
        """ Inserts a cell before the given index. if the index is
        less than or equal to zero insert at the begining. If the
        index is too large, insert at the end
        """

        #Add the event handlers
        wx.EVT_MOUSEWHEEL(cell, self.OnWheel)
        
        index = max(0, index)
        index = min(len(self.celllist), index)
        
        self.celllist.insert(index, cell)
        self.id_dict[cell.GetId()]=index
        def f(x):
            self.id_dict[x.GetId()]+=1
            return None
        map(f,self.celllist[index+1:])
        if update:
            self.RelayoutCells(index)
        return index

    def DeleteCell(self, index, update = True):
        self.celllist[index].Destroy()
        del (self.celllist[index])
        #print "del" #dbg
        #print self.id_dict #dbg
        #print "f" #dbg
        def f(x):
            #print x.GetId() #dbg
            self.id_dict[x.GetId()]-=1
            return None
        map(f, self.celllist[index:]) #TODO: test if this works when index=len(celllist)-1
        if update :
            self.RelayoutCells(index)
        
    def GetCell(self, index=None, id=None):
        if index is None:
            index = self.id_dict[id]
        return self.celllist[index]

    def GetNext(self, index=None, id=None):
        if index is None:
            index = self.id_dict[id]
        if index == len(self.celllist) - 1:
            return None
        else:
            return self.celllist[index+1]

    def GetPrev(self, index=None, id=None):
        if index is None:
            index = self.id_dict[id]
        if index == 0:
            return None
        else:
            return self.celllist[index-1]
    
    def GetIndex(self, id):
        """ Returns the index corresponding to a window id"""
        #print self.id_dict #dbg
        return self.id_dict[id]
    def SetActiveCell (self, index):
        """ Sets the active cell """
        pass
    
    
        

#end wxNotebook 
