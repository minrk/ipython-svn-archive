# Copyright (c) 2001-2004 Twisted Matrix Laboratories.
# See LICENSE for details.
from optparse import OptionParser
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
        wxFrame.__init__(self, parent, ID, title, wxDefaultPosition, 
            wxSize(300, 200))
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


def main(port, allow_ip=None):
    # Setp the twisted server
    allow_list = ['127.0.0.1']
    if allow_ip is not None:
        allow_list.append(allow_ip)    
    log.startLogging(sys.stdout)
    reactor.listenTCP(port, 
        KernelTCPFactoryGUI(allow=allow_list))
    # Start wx, which start the reactor using reactor.interleave
    app = MyApp(0)
    app.MainLoop()


if __name__ == '__main__':
    parser = OptionParser()
    parser.set_defaults(port=10105)
    parser.add_option("-p", "--port", type="int", dest="port",
        help="the TCP port the kernel will listen on")
    parser.add_option("-a", "--allow", dest="allow_ip",
        help="an IP address to allow to connect to the kernel")
    (options, args) = parser.parse_args()
    print "Starting the kernel on port %i" % options.port
    main(options.port, options.allow_ip)
