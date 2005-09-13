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

import os.path
import StringIO

import wx
import wx.html

from nbshell.utils import *
from nbshell import SimpleXMLWriter
from nbshell import RerunDlg

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
ID_EXPORT = id_iter.next()
ID_PRINT_PREVIEW = id_iter.next()
ID_PRINT = id_iter.next()
ID_PAGE_SETUP = id_iter.next()


#NBShell menu identifiers
ID_RERUN = id_iter.next()

#Insert menu identifiers
ID_INSERT_TEXT = id_iter.next()
ID_INSERT_CODE = id_iter.next()
ID_INSERT_FIGURE = id_iter.next()
ID_INSERT_XML = id_iter.next()
ID_DELETE_BLOCK = id_iter.next()

class ipnFrame(wx.Frame):
    def __init__ (self, parent, id, title, pos=wx.DefaultPosition,
                  size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE, name="myframe"):

        wx.Frame.__init__(self, parent, id, title, pos, size, style, name)
        #Here I used to set up printing like this: 
        #
        #self.easyprinting = wx.html.HtmlEasyPrinting() 
        #
        #Unfortunately this gives me stange warnings in my python2.4 (probably
        #haveing something to do with the fact that I don't have a printer ;)
        #So now I set self.easyprinting the first time I use it in one of the
        #printing or previewing methods. --tzanko
        self.easyprinting = None
        
    def SetTitle(self, filename):
        """Adds the filename to the title"""
        wx.Frame.SetTitle(self, " %s %s (%s)"%(Release.name, Release.version,filename))

    def OnInit(self, app):
        self.app = app
        self.notebook = app.notebook
        
        self.CreateStatusBar()
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
        filemenu.Append(ID_EXPORT, "&Export...", "Export the notebook in a printeble format")
        filemenu.AppendSeparator()
        filemenu.Append(ID_PAGE_SETUP, "Page Setup...")
        filemenu.Append(ID_PRINT, "&Print...", "Print the document")
        filemenu.Append(ID_PRINT_PREVIEW, "Print P&review...", "Preview the notebook")
        filemenu.AppendSeparator()
        filemenu.Append(ID_EXIT, "E&xit", "Terminate the program")
        wx.EVT_MENU(self, ID_EXIT, self.OnExit)
        wx.EVT_MENU(self, ID_NEW, self.OnNew)
        wx.EVT_MENU(self, ID_OPEN, self.OnOpen)
        wx.EVT_MENU(self, ID_SAVE, self.OnSave)
        wx.EVT_MENU(self, ID_SAVEAS, self.OnSaveAs)
        wx.EVT_MENU(self, ID_EXPORT, self.OnExport)
        wx.EVT_MENU(self, ID_PAGE_SETUP, lambda evt:self.OnPrint(evt,2))
        wx.EVT_MENU(self, ID_PRINT, lambda evt:self.OnPrint(evt,0))
        wx.EVT_MENU(self, ID_PRINT_PREVIEW, lambda evt:self.OnPrint(evt,1))
                    
        nbshellmenu = wx.Menu()
        nbshellmenu.Append(ID_RERUN, "&Rerun...", "Rerun parts of the notebook")
        wx.EVT_MENU(self, ID_RERUN, self.OnRerun)
        
        insertmenu = wx.Menu()
        insertmenu.Append(ID_INSERT_TEXT, "Insert Text", "Inserts a text block")
        insertmenu.Append(ID_INSERT_CODE, "Insert Code", "Inserts a new empty code block")
        insertmenu.Append(ID_INSERT_FIGURE, "Insert Figure...", "Inserts a figure")
        insertmenu.Append(ID_INSERT_XML, "Insert XML", "Inserts raw xml code block")
        insertmenu.Append(ID_DELETE_BLOCK, "Delete block", "Deletes the currnet block")
        wx.EVT_MENU(self, ID_INSERT_CODE, self.OnInsertCode)
        wx.EVT_MENU(self, ID_INSERT_TEXT, self.OnInsertText)
        wx.EVT_MENU(self, ID_INSERT_FIGURE, self.OnInsertFigure)
        wx.EVT_MENU(self, ID_INSERT_XML, self.OnInsertXML)
        wx.EVT_MENU(self, ID_DELETE_BLOCK, self.OnDeleteBlock)
        
        menu = wx.MenuBar()
        menu.Append(filemenu, "&File")
        menu.Append(insertmenu, "&Insert")
        menu.Append(nbshellmenu, "N&BShell")
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
        self.notebook.SetSize(self.GetClientSizeTuple())
        #self.Layout()

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
                            wildcard = "Notebook files (*.pybk)|*.pybk",style = wx.OPEN)
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
                            wildcard = "Notebook files (*.pybk)|*.pybk",style = wx.SAVE)
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
                
    def OnExport(self, evt = None):
        name = self.app.document.fileinfo['name']
        path = self.app.document.fileinfo['path']
        defaultname = os.path.splitext(name)[0] + '.html'
        dlg = wx.FileDialog(self, "Choose a file",\
                            wildcard ='HTML files (*.htm[l])|*.htm;*html|'+
                            'LaTeX files (*.tex)|*.tex|PDF files (*.pdf)|*.pdf',
                            defaultDir = self.app.document.fileinfo['path'],
                            defaultFile = defaultname,
                            style = wx.SAVE|wx.OVERWRITE_PROMPT|wx.CHANGE_DIR)
        dlg.SetFilterIndex(0) #Set .html files to be default

        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            index = dlg.GetFilterIndex()
            type = {0:'html', 1:'latex', 2:'pdf'}[index]
            try:
                self.app.document.Export(filename, type)
            except Exception, inst:
                #TODO: better error handling
                dlg = wx.MessageDialog(self, "Error: "+str(inst), style = wx.OK)
                dlg.ShowModal()
                raise #dbg
            
    def OnPrint(self, evt = None, type = 0):
        
        tmpfile = os.tmpnam()+'.html'
        try:
            self.app.document.Export(tmpfile,'html')
        except Exception, inst:
            dlg = wx.MessageDialog(self, "Error: "+str(inst), style = wx.OK)
            dlg.ShowModal()
            raise #dbg
        #check the comment in __init__
        if self.easyprinting is None:
            self.easyprinting = wx.html.HtmlEasyPrinting()
        if type == 0:
            self.easyprinting.PrintFile(tmpfile)
        elif type == 1:
            self.easyprinting.PreviewFile(tmpfile)
        elif type == 2:
            self.easyprinting.PageSetup()
        else:
            os.remove(tmpfile)
            raise NotImplementedError
        os.remove(tmpfile)

    def OnRerun(self,evt = None):
        dlg = RerunDlg.RerunDialog(self, -1, 'Choose what to rerun')
        if dlg.ShowModal() == wx.ID_CANCEL:
            return
        choice = dlg.choice
        log = self.app.document.logs[dlg.logid]
        sheet = self.app.document.sheet
        if choice == 0: #Rerun all cells
            log.Reset()
            log.Run(0)
            sheet.Update(update = True, output = True)
        elif choice == 1: #Rerun a slice of cells
            print dlg.slice
            sheet.RerunCells(dlg.logid, log.log[dlg.slice], update = True)
        else: #Rerun a list of cells
            sheet.RerunCells(dlg.logid, 
                             filter(lambda x:x is not None,[log.log[i] for i in dlg.list]),
                             update = True)
        #self.app.document.Rerun()
    
    def OnInsertText(self, evt = None):
        sheet = self.app.document.sheet
        block = sheet.currentcell
        sheet.InsertText(block, default(lambda:block.view.position,0), update = True)
    
    def OnInsertCode(self, evt = None):
        sheet = self.app.document.sheet
        block = sheet.currentcell
        sheet.InsertCode(block, default(lambda:block.view.position,0), update = True)
    
    def OnInsertXML(self, evt = None):
        sheet = self.app.document.sheet
        block = sheet.currentcell
        sheet.InsertXML(block, default(lambda:block.view.position,0), update = True)

        
    def OnInsertFigure(self, evt = None):
        dlg = wx.FileDialog(self, "Choose a Figure", \
                            wildcard = "PNG files (*.png)|*.png",style = wx.OPEN)
        val = dlg.ShowModal()
        if val == wx.ID_CANCEL:
            return None
        else:
            filename = dlg.GetPath()
            sheet = self.app.document.sheet
            text = StringIO.StringIO()
            #We use XMLWriter, to avoid problems with a filename with special symbols,
            #for example: blah.png"/><some random xml code>.png
            writer = SimpleXMLWriter.XMLWriter(text, encoding = 'utf-8')
            writer.start('ipython-figure', type = "png", filename = filename)
            writer.end()
            block = sheet.currentcell
            sheet.InsertFigure(block, default(lambda:block.view.position,0),
               figurexml = text.getvalue())
            text.close()
            
    def OnDeleteBlock(self, evt = None):
        sheet = self.app.document.sheet
        sheet.DeleteCell(sheet.currentcell)


