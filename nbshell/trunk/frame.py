""" Contains the main frame of the application """
import wx

ID_NEW = wx.ID_NEW
ID_OPEN  = wx.ID_OPEN
ID_SAVE = wx.ID_SAVE
ID_SAVEAS = wx.ID_SAVEAS
ID_EXIT = wx.ID_EXIT
ID_ABOUT = wx.ID_ABOUT
class ipnFrame(wx.Frame):
    def __init__ (self, parent, id, title, pos=wx.DefaultPosition,
                  size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE, name="myframe"):

        wx.Frame.__init__(self, parent, id, title, pos, size, style, name)

    def OnInit(self, app):
        self.app = app
        self.notebook = app.notebook
     
#        self.sizer = wx.BoxSizer(wx.VERTICAL)
#        self.sizer.Add(self.notebook, 1, wx.EXPAND)

#        self.SetSizer(self.sizer)
        self.SetUpMenu()
#        self.sizer.Fit(self)
        wx.EVT_SIZE(self, self.OnSize)

    def SetUpMenu(self):
        """ Sets up the menu. """
        #TODO: this is ugly, how can I make it better?
        filemenu = wx.Menu()
        filemenu.Append(ID_NEW, "&New", "New file")
        filemenu.Append(ID_OPEN, "&Open...", "Opens file")
        filemenu.Append(ID_SAVE, "&Save", "Save file")
        filemenu.Append(ID_SAVEAS, "Save &As...", "Save file with new name")
        filemenu.AppendSeparator()
        filemenu.Append(ID_EXIT, "E&xit", "Terminate the program")
        wx.EVT_MENU(self, ID_EXIT, self.OnExit)
        wx.EVT_MENU(self, ID_NEW, self.OnNew)
        wx.EVT_MENU(self, ID_OPEN, self.OnOpen)
        wx.EVT_MENU(self, ID_SAVE, self.OnSave)
        wx.EVT_MENU(self, ID_SAVEAS, self.OnSaveAs)
        menu = wx.MenuBar()
        menu.Append(filemenu, "&File")
        self.SetMenuBar(menu)

    def OnExit(self, evt):
        self.Close()
        
    def OnSize (self, evt):
        self.Layout()

    def OnNew(self, evt):
        """Creates a new untitled document"""
        if(self.app.document.IsModified()):
            dlg = wx.MessageDialog(self, "The document has been modified. Do you want to save your changes?",
                                   "IPN 0.1", style = wx.YES_NO|wx.CANCEL)
            val = dlg.ShowModal()
            if val == wx.ID_CANCEL:
                return None
            if val == wx.ID_YES:
                self.OnSave(evt) #well, the parameter is unused
        self.app.document.DefaultNotebook()

        
    def OnOpen(self, evt):
        if(self.app.document.IsModified()):
            dlg = wx.MessageDialog(self, "The document has been modified. Do you want to save your changes?",
                                   "IPN 0.1", style = wx.YES_NO|wx.CANCEL)
            val = dlg.ShowModal()
            if val == wx.ID_CANCEL:
                return None
            if val == wx.ID_YES:
                self.OnSave(evt) #well, the parameter is unused
        dlg = wx.FileDialog(self, "Choose a File", \
                            wildcard = "Notebook files (*.nbk)|*.nbk",style = wx.OPEN)
        val = dlg.ShowModal()
        if val == wx.ID_CANCEL:
            return None
        else:
            filename = dlg.GetPath()
            try:
                self.app.document.LoadFile(filename, overwrite = True)
            except Exception, inst:
                #print repr(inst) #dbg
                dlg = wx.MessageDialog(self, "Error: "+str(inst), style = wx.OK)
                dlg.ShowModal()
                #raise #dbg
                return None

    def OnSave(self, evt):
        if self.app.document.fileinfo['untitled'] == True:
            self.OnSaveAs(self,evt)
        else:
            try:
                self.app.document.SaveFile()
            except Exception, inst:
                #print repr(inst) #dbg
                dlg = wx.MessageDialog(self, "Error: "+str(inst), style = wx.OK)
                dlg.ShowModal()
                #raise #dbg
    
    def OnSaveAs(self, evt):
        dlg = wx.FileDialog(self, "Choose a File", \
                            defaultDir = self.app.document.fileinfo['path'],\
                            defaultFile = self.app.document.fileinfo['name'],\
                            wildcard = "Notebook files (*.nbk)|*.nbk",style = wx.SAVE)
        val = dlg.ShowModal()
        if val == wx.ID_CANCEL:
            return None
        else:
            filename = dlg.GetPath()
            try:
                self.app.document.SaveFile(filename)
            except Exception, inst:
                #print repr(inst) #dbg
                dlg = wx.MessageDialog(self, "Error: "+str(inst), style = wx.OK)
                dlg.ShowModal()
                #raise #dbg
                return None

