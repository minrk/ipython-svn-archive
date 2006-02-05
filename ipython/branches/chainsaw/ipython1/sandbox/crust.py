"""Crust combines the shell and filling into one control."""

__author__ = "Patrick K. O'Brien <pobrien@orbtech.com>"
__cvsid__ = "$Id: crust.py,v 1.9 2004/10/15 20:31:23 RD Exp $"
__revision__ = "$Revision: 1.9 $"[11:-2]

import wx

import os
import pprint
import sys

import wx.py.dispatcher as dispatcher
import wx.py.editwindow as editwondow
from wx.py.filling import Filling
import wx.py.frame as frame
from wx.py.shell import Shell
from wx.py.version import VERSION

from wx.py.crust import *

class PIPCrustFrame(frame.Frame):
    """Frame containing all the PyCrust components."""

    name = 'CrustFrame'
    revision = __revision__

    def __init__(self, parent=None, id=-1, title='Parallel IPython Crust',
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.DEFAULT_FRAME_STYLE,
                 rootObject=None, rootLabel=None, rootIsNamespace=True,
                 locals=None, InterpClass=None, *args, **kwds):
        """Create CrustFrame instance."""
        frame.Frame.__init__(self, parent, id, title, pos, size, style)
        intro = 'Twisted Enabled PyCrust for Parallel IPython'
        self.SetStatusText(intro.replace('\n', ', '))
        
        # Import twisted stuff
        from twisted.internet import threadedselectreactor
        threadedselectreactor.install()
        from twisted.internet import reactor
        from twisted.python import log
        self.reactor = reactor
        log.startLogging(sys.stdout)        

        # Pass the reactor to the user namespace
        mylocals = locals
        if mylocals is None:
            mylocals = {'reactor':reactor}
        else:
            mylocals.update({'reactor':reactor})            
        
        self.crust = Crust(parent=self, intro=intro,
                           rootObject=rootObject,
                           rootLabel=rootLabel,
                           rootIsNamespace=rootIsNamespace,
                           locals=mylocals,
                           InterpClass=InterpClass, *args, **kwds)
        self.shell = self.crust.shell
        # Override the filling so that status messages go to the status bar.
        self.crust.filling.tree.setStatusText = self.SetStatusText
        # Override the shell so that status messages go to the status bar.
        self.shell.setStatusText = self.SetStatusText
        # Fix a problem with the sash shrinking to nothing.
        self.crust.filling.SetSashPosition(200)
        # Set focus to the shell editor.
        self.shell.SetFocus()

        # Add a File->Exit event to shutdown the twisted reactor
        mb = self.GetMenuBar()
        m0 = mb.GetMenu(0)
        m0.Append(10101,"E&xit","Exit")
        wx.EVT_MENU(self, 10101, self.DoExit)
        
        # Lastly interleave the twisted reactor with wx!
        reactor.interleave(wx.CallAfter)

    def DoExit(self, event):
        """This is called upon exiting and insures the reactor is stopped."""
        self.reactor.addSystemEventTrigger('after', 'shutdown', 
            self.Close, True)
        self.reactor.stop()

    def OnClose(self, event):
        """Event handler for closing."""
        self.crust.shell.destroy()
        self.Destroy()

    def OnAbout(self, event):
        """Display an About window."""
        title = 'About PyCrust'
        text = 'PyCrust %s\n\n' % VERSION + \
               'Yet another Python shell, only flakier.\n\n' + \
               'Half-baked by Patrick K. O\'Brien,\n' + \
               'the other half is still in the oven.\n\n' + \
               'Shell Revision: %s\n' % self.shell.revision + \
               'Interpreter Revision: %s\n\n' % self.shell.interp.revision + \
               'Platform: %s\n' % sys.platform + \
               'Python Version: %s\n' % sys.version.split()[0] + \
               'wxPython Version: %s\n' % wx.VERSION_STRING + \
               ('\t(%s)\n' % ", ".join(wx.PlatformInfo[1:])) 
        dialog = wx.MessageDialog(self, text, title,
                                  wx.OK | wx.ICON_INFORMATION)
        dialog.ShowModal()
        dialog.Destroy()
