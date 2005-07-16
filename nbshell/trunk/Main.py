""" This module is used currently only for testing. """
import os
import re
import wxversion
wxversion.select('2')
import wx
from ipnNotebookWidget import * # in case you wonder ipn comes from Interactive Python Notebook 
from ipnDocument import *
from frame import ipnFrame


        
class App(wx.App):
    """Application class."""
    
    plugin_dir = "." #this should be configured somewhere
    plugin_dict = {0:0}
    def RegisterPlugins(self):
        """Seeks for plugins and gets their factory objects"""
        dirlist = os.listdir(self.plugin_dir)
        regexpr = re.compile('\.py$') #TODO: check if this works for Unicode
        modlist = filter(lambda x:regexpr.search(x)!=None,dirlist) 
        print modlist
        for module in modlist:
            try:
                dict = globals().copy()
                print "BEFORE"
                #print dict
                print module[0:-3]
                exec "from "+module[0:-3] +" import GetPluginFactory\nprint \"()()()()()()\"" in dict
                print "AFTER"
                #print dict
    #            print "AAAFTER, module=",module
            except:
                if module[0:-3]=="PythonPlugin":
                    raise
            else:
                factory = dict["GetPluginFactory"]()
                print factory.GetString()
                self.plugin_dict[factory.GetString()]=factory

    
    def OnInit(self):
        self.RegisterPlugins()
        self.frame = ipnFrame(None, -1, "wxNotebook Test Frame", size = (400, 300))
        self.notebook = ipnNotebook(self.frame, -1, size = self.frame.GetClientSizeTuple(), style = wx.VSCROLL|wx.HSCROLL)
        self.document = ipnDocument(self, self.notebook)
        self.frame.OnInit(self)
        self.frame.Show()
        self.SetTopWindow(self.frame)
        self.Demo()
        return True

  
    def Demo(self):
        #         self.document.LoadFile("./test.py")
        #        print "inserting 0"
        #        self.document.InsertCell("plaintext", "The new and improved plugin system works")
        #        print "inserting 1"
        #        self.document.InsertCell("plaintext", "Hooray!")
        #        print "updating"

        log = self.document.logs["default-log"]
        log.Append("\n")
        cell = self.document.InsertCell("python")
        cell.data = [(0,0)]
        cell.view.Update()
        self.notebook.Update()



def main():
    app = App()
    app.MainLoop()

if __name__ == '__main__':
    main()
