"""An ipython kernel that is integrated with the wxPython event loop.

This kernel is designed for users who want to use wxPython interactively from
within ipython.  When this kernel is running, the user can import wx and then
interactively create and use wx widgets.  

This kernel should only be used if wx integration is needed.  This is because
this kernel lacks many features that the default kernel has, such as being
multithreaded and having a computational queue.

This module is meant to be run from the command line.  To start the kernel,
issue the command:

    python kernelwx.py

This will start the kernel listening on port 10105 (the default) and will allow
connections from only the localhost (127.0.0.1).  Here is an example that starts
the kernel on port 10106 and allows connections from the localhost and 
121.122.123.124:

    python kernelwx.py -p 10106 -a 121.122.123.124

For more information on the command line options, run:

    python kernelwx.py -h

NOTE:  The kernel cannot currently be run in the background, so:

    python kernelwx.py &

won't result in a running kernel instance.

NOTE:  On Mac OS X, the command pythonw must be used instead of python.
"""

#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************
from optparse import OptionParser
import sys

from wxPython.wx import *

from twisted.internet import threadedselectreactor, protocol, defer
threadedselectreactor.install()
from twisted.internet import reactor
from twisted.python import log

try:
    try:
        from ipython.kernel.kernelcore import KernelTCPFactoryGUI
    except ImportError:
        from kernel.kernelcore import KernelTCPFactoryGUI
except ImportError:
    from kernelcore import KernelTCPFactory

#from kernelcore import KernelTCPFactoryGUI

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
