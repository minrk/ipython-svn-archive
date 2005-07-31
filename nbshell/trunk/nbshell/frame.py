""" Contains the main frame of the application """

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

def idgen():
    id = wx.ID_HIGHEST
    while True:
        id +=1
        yield id
id_iter = idgen()

#File menu identifiers
ID_NEW = wx.ID_NEW
ID_OPEN  = wx.ID_OPEN
ID_SAVE = wx.ID_SAVE
ID_SAVEAS = wx.ID_SAVEAS
ID_EXIT = wx.ID_EXIT
ID_ABOUT = wx.ID_ABOUT

#NBShell menu identifiers
ID_RERUN = id_iter.next()

class ipnFrame(wx.Frame):
    def __init__ (self, parent, id, title, pos=wx.DefaultPosition,
                  size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE, name="myframe"):

        wx.Frame.__init__(self, parent, id, title, pos, size, style, name)
        
    def SetTitle(self, filename):
        """Adds the filename to the title"""
        wx.Frame.SetTitle(self, " %s %s (%s)"%(Release.name, Release.version,filename))

    def OnInit(self, app):
        self.app = app
        self.notebook = app.notebook
     
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.notebook, 1, wx.EXPAND)

        self.SetSizer(self.sizer)
        self.SetUpMenu()
        #self.sizer.Fit(self)
        wx.EVT_SIZE(self, self.OnSize)
        wx.EVT_CLOSE(self, self.OnClose)

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
        
        nbshellmenu = wx.Menu()
        nbshellmenu.Append(ID_RERUN, "&Rerun", "Rerun the notebook")
        wx.EVT_MENU(self, ID_RERUN, self.OnRerun)
        menu = wx.MenuBar()
        menu.Append(filemenu, "&File")
        menu.Append(nbshellmenu, "&NBShell")
        self.SetMenuBar(menu)

    def OnClose(self, evt):
        """This method is called by self.Close(). Do not call it explicitly"""
        if(self.app.document.IsModified()):
            dlg = wx.MessageDialog(self, "The document has been modified. Do you want to save your changes?",
                                   "%s %s"%(Release.name, Release.version), style = wx.YES_NO|wx.CANCEL)
            val = dlg.ShowModal()
            if val == wx.ID_CANCEL:
                return None
            if val == wx.ID_YES:
                self.OnSave(evt) #well, the parameter is unused
        self.Destroy()
        
    def OnExit(self, evt):
        self.Close()
        
    def OnSize (self, evt):
        self.Layout()

    def OnNew(self, evt = None):
        """Creates a new untitled document"""
        if(self.app.document.IsModified()):
            dlg = wx.MessageDialog(self, "The document has been modified. Do you want to save your changes?",
                                   "%s %s"%(Release.name, Release.version), style = wx.YES_NO|wx.CANCEL)
            val = dlg.ShowModal()
            if val == wx.ID_CANCEL:
                return None
            if val == wx.ID_YES:
                self.OnSave(evt) #well, the parameter is unused
        self.app.document.DefaultNotebook()
        self.SetTitle(self.app.document.fileinfo['name'])

        
    def OnOpen(self, evt = None):
        if(self.app.document.IsModified()):
            dlg = wx.MessageDialog(self, "The document has been modified. Do you want to save your changes?",
                                   "%s %s"%(Release.name, Release.version), style = wx.YES_NO|wx.CANCEL)
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
                raise #dbg
                return None
            else:
                self.SetTitle(self.app.document.fileinfo['name'])

    def OnSave(self, evt = None):
        if self.app.document.fileinfo['untitled'] == True:
            self.OnSaveAs(evt)
        else:
            try:
                self.app.document.SaveFile()
            except Exception, inst:
                #print repr(inst) #dbg
                dlg = wx.MessageDialog(self, "Error: "+str(inst), style = wx.OK)
                dlg.ShowModal()
                raise #dbg
    
    def OnSaveAs(self, evt = None):
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
                raise #dbg
                return None
            else:
                self.SetTitle(self.app.document.fileinfo['name'])
                self.app.document.fileinfo['untitled'] = False
                
    def OnRerun(self,evt):
        self.app.document.Rerun()
