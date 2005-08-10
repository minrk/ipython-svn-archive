""" Main nbshell module. To run nbshell simply type
    > python2.4 Main.py 
"""

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

import sys
import os
import re
try:
    import wxversion
    wxversion.ensureMinimal('2.5.3')
except:
    pass #I will try to run it, but it might not work

import wx

import utils
from nbshell import ipnNotebookWidget,ipnDocument,frame
from ipnNotebookWidget import * # in case you wonder ipn comes from Interactive Python Notebook 
from ipnDocument import *
from frame import ipnFrame


        
class App(wx.App):
    """Application class."""
    
    plugin_dir = "." #this should be configured somewhere
    plugin_dict = {0:0}
    
    def __init__(self, *args, **kwds):
        wx.App.__init__(self, *args, **kwds)
        self.mainloop = False
        
    def RegisterPlugins(self):
        """Seeks for plugins and gets their factory objects"""
        #dirlist = os.listdir(self.plugin_dir)
        #regexpr = re.compile('\.py$') #TODO: check if this works for Unicode
        #modlist = filter(lambda x:regexpr.search(x)!=None,dirlist) 
        ##print modlist #dbg
        #for module in modlist:
        #    try:
        #        dict = globals().copy()
        #        exec "from nbshell."+module[0:-3] +" import GetPluginFactory" in dict
        #    except:
        #        if module[0:-3]=="PythonPlugin":
        #            raise
        #    else:
        #        factory = dict["GetPluginFactory"]()
        #        #print factory.GetString() #dbg
        #        self.plugin_dict[factory.string]=factory

        # Currently there are only three plugins, so we simply add them
        from nbshell.PythonPlugin import GetPluginFactory
        factory = GetPluginFactory()
        self.plugin_dict[factory.string] = factory
        from nbshell.PlainTextPlugin import GetPluginFactory
        factory = GetPluginFactory()
        self.plugin_dict[factory.string] = factory
        from nbshell.FigurePlugin import GetPluginFactory
        factory = GetPluginFactory()
        self.plugin_dict[factory.string] = factory
        del(GetPluginFactory)

    
    def OnInit(self):
        self.RegisterPlugins()
        self.frame = ipnFrame(None, -1, "", size = (640, 480))
        self.notebook = ipnNotebook(self.frame, -1, size = self.frame.GetClientSizeTuple(), style = wx.VSCROLL|wx.HSCROLL)
        self.document = ipnDocument(self, self.notebook)
        self.frame.OnInit(self)
        self.frame.Show()
        self.SetTopWindow(self.frame)
        self.frame.OnNew()
        #self.Demo()
        return True

  
    def Demo(self):
        #         self.document.LoadFile("./test.py")
        #        print "inserting 0"
        #        self.document.InsertCell("plaintext", "The new and improved plugin system works")
        #        print "inserting 1"
        #        self.document.InsertCell("plaintext", "Hooray!")
        #        print "updating"

        #        log = self.document.logs["default-log"]
        #        log.Append("\n")
        #        print self.document.sheet.element
        #        block = etree.SubElement(self.document.sheet.element, 'ipython-block', logid='default-log')
        #        etree.SubElement(block, 'ipython-input', number='0')
        #        cell = self.document.InsertCell("python", ipython_block=block)
        #        cell.view.Update()
        #        self.notebook.Update()
        
        try:
            file = sys.argv[1]
        except:
            file = 'test2.nbk'
            
        self.document.LoadFile(file)
        
    def MainLoop(self):
        """The main loop method of the application."""
        #The matplotlib WX backend calls MainLoop() in the show() function.
        #Since the main loop has already started this call is unwanted.
        #So I make the main loop to be called only once
        if not self.mainloop:
            self.mainloop = True
            wx.App.MainLoop(self)


def start():
    app = App(redirect=False)
    app.MainLoop()

if __name__ == '__main__':
    start()
