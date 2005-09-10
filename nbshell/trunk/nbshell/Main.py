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

from nbshell.utils import delta_time

import sys
import os
import re
from optparse import OptionParser
import unittest

delta_time('standard modules loaded') #dbg
#wxversion messes up with the sys.path. so I have to fix it
oldpath = sys.path[0]
try:
    import wxversion
    wxversion.ensureMinimal('2.5.3')
except:
    pass #I will try to run it, but it might not work
sys.path[0:0] = [oldpath]
import wx
delta_time('wx loaded') #dbg

from nbshell.utils import *
from nbshell import ipnNotebookWidget,ipnDocument,frame,tester
from ipnNotebookWidget import * # in case you wonder ipn comes from Interactive Python Notebook 
from ipnDocument import *
from frame import ipnFrame
delta_time('nbshell modules loaded') #dbg

from IPython import ultraTB
# For developer use: let's park a nice formatted traceback printer in
# here.  Once this becomes more stable we can use a CrashHandler, but
# for now this will be nice to get feedback.
sys.excepthook = ultraTB.FormattedTB(mode='Context',color_scheme='Linux')
#test the excepthook
class App(wx.App):
    """Application class."""
    
    plugin_dir = "." #this should be configured somewhere
    plugin_dict = {0:0}
    
    def __init__(self, *args, **kwds):
        wx.App.__init__(self, *args, **kwds)
        self.mainloop = False
        self.test = False
        
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
        return True

  
    def Test(self):
        suite = tester.suite
        unittest.TextTestRunner().run(suite)

        self.frame.Close()
        return True

        
        
    def MainLoop(self):
        """The main loop method of the application."""
        #The matplotlib WX backend calls MainLoop() in the show() function.
        #Since the main loop has already started this call is unwanted.
        #So I make the main loop to be called only once

        if self.test:
            self.Test()
        if not self.mainloop:
            self.mainloop = True
            wx.App.MainLoop(self)


def start():
    #Parse options
    parser = OptionParser()
    parser.add_option('-t', '--test', action = 'store_true', dest = 'test')
    (options, args) = parser.parse_args()
    app = App(redirect=False)
    #If test option is set, we test the application
    app.test = default(lambda:options.test,False)
    app.MainLoop()

if __name__ == '__main__':
    start()
