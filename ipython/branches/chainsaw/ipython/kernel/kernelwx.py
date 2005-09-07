# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.

import sys

from wxPython.wx import *

from twisted.internet import threadedselectreactor, protocol, defer
threadedselectreactor.install()
from twisted.internet import reactor
from twisted.python import log

from kernelcore import KernelTCPFactoryGUI

# Here are the classes for wxPython

ID_EXIT  = 101

class MyFrame(wxFrame):
    def __init__(self, parent, ID, title):
        wxFrame.__init__(self, parent, ID, title, wxDefaultPosition, wxSize(300, 200))
        menu = wxMenu()
        menu.Append(ID_EXIT, "E&xit", "Terminate the program")
        menuBar = wxMenuBar()
        menuBar.Append(menu, "&File")
        self.SetMenuBar(menuBar)
        EVT_MENU(self, ID_EXIT,  self.DoExit)

        reactor.interleave(wxCallAfter)

    def DoExit(self, event):
        reactor.addSystemEventTrigger('after', 'shutdown', self.Close, true)
        reactor.stop()


class MyApp(wxApp):

    def OnInit(self):
        frame = MyFrame(NULL, -1, "IPython Kernel: wxPython Enabled")
        frame.Show(true)
        self.SetTopWindow(frame)
        return true


def main(port):
    # Setp the twisted server
    log.startLogging(sys.stdout)
    reactor.suggestThreadPoolSize(5)
    reactor.listenTCP(port, 
        KernelTCPFactoryGUI(allow=['127.0.0.1']))
    # Start wx, which start the reactor using reactor.interleave
    app = MyApp(0)
    app.MainLoop()


if __name__ == '__main__':
    port = int(sys.argv[1])
    main(port)
