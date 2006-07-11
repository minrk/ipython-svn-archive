"""Shell is an interactive text control in which a user types in
commands to be sent to the interpreter.  This particular shell is
based on wxPython's wxStyledTextCtrl.

Sponsored by Orbtech - Your source for Python programming expertise."""

__author__ = "Patrick K. O'Brien <pobrien@orbtech.com>"
__cvsid__ = "$Id: shell.py,v 1.9 2004/10/15 20:31:23 RD Exp $"
__revision__ = "$Revision: 1.9 $"[11:-2]

import wx
from wx import stc

import keyword
import os
import sys
import time

from wx.py.buffer import Buffer
import wx.py.dispatcher as dispatcher
import wx.py.editwindow as editwindow
import wx.py.frame as frame
from wx.py.pseudo import PseudoFileIn
from wx.py.pseudo import PseudoFileOut
from wx.py.pseudo import PseudoFileErr
from wx.py.version import VERSION

from wx.py.shell import *

class PIPShellFrame(frame.Frame):
    """Frame containing the shell component."""

    name = 'Shell Frame'
    revision = __revision__

    def __init__(self, parent=None, id=-1, title='Parallel IPython Shell',
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.DEFAULT_FRAME_STYLE, locals=None,
                 InterpClass=None, *args, **kwds):
        """Create ShellFrame instance."""
        frame.Frame.__init__(self, parent, id, title, pos, size, style)
        intro = 'Twisted Enabled PyShell for Parallel IPython'
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

        # Now creat a Shell object
        self.shell = Shell(parent=self, id=-1, introText=intro,
                           locals=mylocals, InterpClass=InterpClass,
                           *args, **kwds)
                                                      
        # Override the shell so that status messages go to the status bar.
        self.shell.setStatusText = self.SetStatusText
        
        # Add a File->Exit event to shutdown the twisted reactor
        mb = self.GetMenuBar()
        m0 = mb.GetMenu(0)
        m0.Append(10101,"E&xit","Exit")
        wx.EVT_MENU(self, 10101, self.DoExit)
        
        # Lastly interleave the twisted reactor with wx!
        reactor.interleave(wx.CallAfter)


    def DoExit(self, event):
        self.reactor.addSystemEventTrigger('after', 'shutdown', 
        self.Close, True)
        self.reactor.stop()

    def OnClose(self, event):
        """Event handler for closing."""
        # This isn't working the way I want, but I'll leave it for now.
        if self.shell.waiting:
            if event.CanVeto():
                event.Veto(True)
        else:
            self.shell.destroy()
            self.Destroy()

    def OnAbout(self, event):
        """Display an About window."""
        title = 'About PyShell'
        text = 'PyShell %s\n\n' % VERSION + \
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


