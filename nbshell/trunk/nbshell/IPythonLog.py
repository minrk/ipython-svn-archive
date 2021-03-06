""" IPythonLog.py Contains a IPythonLog class which holds the information of one log"""

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
import sys
import StringIO
import textwrap
import __builtin__
import pprint

from wx.py.buffer import Buffer
import wx.py.dispatcher
from wx.py import editwindow
import wx.py.frame
from wx.py.pseudo import PseudoFileIn
from wx.py.pseudo import PseudoFileOut
from wx.py.pseudo import PseudoFileErr
#from wx.py.version import VERSION

from IPython import Shell
from IPython import genutils
from IPython.Magic import Macro
from notabene import notebook

from lxml import etree

from nbshell.utils import *

#TODO: Fix the plotting API
from nbshell.plotting_backends import matplotlib_backend as backend


class IPythonLog(object):
    def __init__(self, doc, nbk, logid, *args, **kwds):
        self.doc = doc
        self.notebook = nbk
        self.log = nbk.get_log(logid) 
        self.logid = logid #this is also self.log.id
        self.last = False
        self._lastcell = None #used by self.lastcell

        #set up wrapper to use for long output
        self.wrapper = textwrap.TextWrapper()

        #Here I will sort the cells, according to their numbers
        #self.log.element[:] = sorted(self.log, key = lambda x:int(x.attrib['number']))
        #XXX modifies the xml element(tree) that nb Log wraps so it may be bad
        #then again, as log.cells is a list (array),
        #as far as i can see the elements are always sorted already
        #(so that sorting never does anything in the current impl, right?)
        
        #Set up plotting
        self.plot_api = backend.PlotLibraryInterface(self.filename_iter())
        #Set up the interpreter
        #For now we will keep our own excepthook
        self.stdin_orig = sys.stdin
        self.stdout_orig = sys.stdout
        self.stderr_orig = sys.stderr
        self.excepthook_orig = sys.excepthook
        import __builtin__
        __builtin__.close = __builtin__.exit = __builtin__.quit = \
                   'Click on the close button to leave the application.'

        user_ns =  {'__name__'     :'__main__',\
                    '__builtins__' : __builtin__,\
                    '__app':self.doc.app
                    }
        user_ns['grab_figure'] = self.grab_figure
        
        #I'll keep that for now, if we decide to go with initialization in profiles
        #        # XXX Hack to preload matptlotlib.  This will be moved out once we
        #        # have restored ipython's profile support
        #
        #        mplstart = """
        #from pylab import *
        #switch_backend('WXAgg')
        #ion()
        #"""
        #        exec mplstart in user_ns
        excepthook_orig = sys.excepthook
        self.interp = Shell.IPShellGUI(argv=['-colors','NoColor'], user_ns=user_ns)

        self.interp_log = self.interp.IP.log
        def donothing(*args, **kwds):
            pass
        self.interp.IP.log = donothing
        del self.interp.IP.input_hist[0]

        self.excepthook_IP = sys.excepthook
        sys.excepthook = excepthook_orig
        #Set up the number 0 cell. It is used for code which is not supposed to
        #be edited. And it has to be hidden
        #etree.dump(self.log) #dbg
        if not self.log:  
            #This is a new log  
            self.Append(input="""  
############DO NOT EDIT THIS CELL############  
from pylab import *  
switch_backend('WXAgg')  
ion()  
""", number = 0)  
            self.Run()  
        elif self.log[0] is not None:
            self.__run(self.Get(0))
            
        #Append the empty element at the end
        self.SetLastInput()

        del __builtin__

        #end shell initialization

        
    def filename_iter(self):
        """A generator function used for generating unique figure filenames"""
        counter = 1
        fn = self.doc.fileinfo['path'] + '/' + os.path.splitext(self.doc.fileinfo['name'])[0]
        while True:
            yield "%s_%d.png"%(fn,counter)
            counter+=1
    
    def grab_figure(self,number=None,caption=None,dpi=None):
        """Call this to grab the figure currently being edited and put it in
        the notebook"""
        figurexml = self.plot_api.grab_png(number,caption,dpi)
        #Append the new figure to the appropriate figure list in the log
        #The figure lists will be dealt with in UpdateOutput
        if figurexml is not None:
            figuredict = getattr(self, 'figuredict', {})
            figurelist = figuredict.get(self.currentcell.number, [])
            figurelist.append(figurexml)
            figuredict[self.currentcell.number] = figurelist
            self.figuredict = figuredict
        
        
    # TODO:All logs have one cell with empty input. This is the cell where the
    # user will insert an input. Since this cell should not be part of the
    # notebook file it is deleted before the file is saved. The two methods
    # below are used for inserting and deleting this cell. However, there is
    # some spagetti code here, because ProcessLine() also appends a new empty
    # input after it has run the current input. Fix this
    def SetLastInput(self):
        """Append a cell with an empty input at the end of the log. This is
        called whenever a log is created."""
        if not self.last:
            self.Append(input = '\n\n')
            self.last = True
        
    def ClearLastInput(self):
        """Clear the empty input at the end of the log."""
        if self.last:
            self.log.remove(self.log[-1].number)
            self.last = False
    
    lastcell = property(fget = lambda self:self.notebook.get_last_cell(self.logid))
            
    #TODO: I should support interactive input. Fix this.
    def readline(self, size):
        return ""
    def readlines(self, sizehint):
        return ""
    def raw_input(self, prompt = None):
        return ""
    
    def writeOut(self, text):
        """Write to the output of the current cell"""
        oldtext = self.lastcell.stdout or ''
        self.lastcell.stdout = oldtext + text

    def writeErr(self, text):
        oldtext = self.lastcell.stderr or ''
        self.lastcell.stderr = oldtext + text

    
    def Append(self, input, output = None, number = 0):
        """Adds a new cell with the given input at the end of the list.
        Returns the cell. Number is used only if the log is empty."""
        if self.log:
            number = self.lastcell.number+1
        try:
            newcell = self.log.add(number)
        except ValueError: #happened due to my (antont) bug in PythonPlugin
            #i guess still ok to leave here to be sure?
            print "Warning: IPythonLog tried to recreate cell num", number, "- ignoring the append"
            #number += 1
            #self.notebook.add_cell(number)
            return self.lastcell
        #Now self.lastcell points to the new cell
        newcell.input = input
        if output is not None:
            newcell.output = output
        return newcell #newcell == self.lastcell
    
    def Remove(self, number):
        """Removes the cell with the given number from the log."""
        self.log.remove(number)
        
    def Clear(self):
        self.log.clear()
        self.Reset()
        self.Append(input="""############DO NOT EDIT THIS CELL############
from pylab import *
switch_backend('WXAgg')
ion()
""", number = 0)
        self.Run()

        
    def Get(self, number): 
        """Returns the cell with the given number"""
        return self.log[number]
        
    def Run(self, number = None):
        """ This method will run the code in all cells with numbers larger or
        equal to number. If number is None it will run only the last cell.
        Internally it uses __run. Returns True, if the input is processed,
        False if it needs more input."""
        
        if number == None:
            return self.__run(self.lastcell)
        cells = self.log[int(number):]
        for cell in cells:
            if not self.__run(cell):
                return False
        return True
        
    def Reset(self):
        """ Resets the interpreter, namespace etc """
        self.interp.reset()
        pass
        
    def __run(self, cell):
        """ This methods runs the input lines. """
        #print 'running code...' #dbg
        #delta_time('__run: start')
        print 'In[%d]: '%cell.number,cell.input #dbg
        self.output = '' #used by displayhook to store output
        cout = StringIO.StringIO()
        cerr = StringIO.StringIO()
        #self.currentcell points to cell for grab_figure to use
        #TODO:this could be prettier
        self.currentcell = cell

        # Add the whole input to the input history (ignoring the leading and
        # trailing '\n')
        self.interp_log(cell.input[1:-1], False)

        #The first and last characters of cell.input are '\n'
        retval = self.interp.runlines(cell.input[1:-1],\
                                      displayhook = self.displayhook,\
                                      stdout = cout, stderr = cerr)
        #delta_time('__run: code run') #dbg
        #Retrieve stdout
        text = '\n' + cout.getvalue()
        #print 'unformatted stdout ->', text #dbg
        if text != '\n':
            #if text[-1] != '\n':
            #    text = text + '\n'
            cell.stdout =''.join(['\n'.join(self.wrapper.wrap(x))+'\n'\
                                  for x in text.splitlines(False)]) #wrap stdout
        cout.close()
        #delta_time('__run: handled stdout') #dbg
        #Retrieve stderr
        text = '\n' + cerr.getvalue()
        #print 'unformatted stderr ->', text #dbg
        if text != '\n':
            #if text[-1] != '\n':
            #    text = text + '\n'
            cell.stderr = ''.join(['\n'.join(self.wrapper.wrap(x))+'\n'\
                                  for x in text.splitlines(False)]) #wrap stderr
        cerr.close()
        #delta_time('__run: handled stderr') #dbg
        
        if self.output != '':
            cell.output = ''.join(['\n'.join(self.wrapper.wrap(x))+'\n'\
                                   for x in self.output.splitlines(False)]) #wrap the output
            #print 'wrapped output ->', self.output.text #dbg
        #delta_time('__run: handled output') #dbg

        print 'Out[%d]: '%cell.number, cell.output #dbg
        print 'Stdout[%d]: '%cell.number, cell.stdout #dbg
        print 'Stderr[%d]: '%cell.number, cell.stderr #dbg

        #TODO: the return value of runlines should match the return value of __run
        if retval: 
            return False
        else:
            return True
        
    def displayhook(self, obj):
        # RTK: modified from IPython.Prompts.CachedOutput.__call__()
        
        slf = self.interp.IP.outputcache
        slf.prompt_count = self.currentcell.number

        #print >> self.stdout_orig,  'displayhook called' #dbg
        # We want to keep only the last output
        if obj is not None:
            if slf.Pprint:
                self.output = '\n%s\n' % pprint.pformat(obj)
            else:
                self.output = '\n%r\n' % obj

        # If something injected a '_' variable in __builtin__, delete
        # ipython's automatic one so we don't clobber that.  gettext() in
        # particular uses _, so we need to stay away from it.
        if '_' in __builtin__.__dict__:
            try:
                del slf.user_ns['_']
            except KeyError:
                pass
        if obj is not None:
            cout_write = genutils.Term.cout.write # fast lookup
            # first handle the cache and counters
            slf.update(obj)
            # do not print output if input ends in ';'
            if slf.input_hist[slf.prompt_count].endswith(';\n'):
                return
            # don't use print, puts an extra space
            #cout_write(slf.output_sep)
            #if slf.do_full_cache:
            #    cout_write(str(slf.prompt_out))

            if isinstance(obj,Macro):
                print 'Executing Macro...'
                # in case the macro takes a long time to execute
                genutils.Term.cout.flush()
                exec obj.value in slf.user_ns
                return None

            # and now call a possibly user-defined print mechanism
            #slf.display(obj)
            #cout_write(slf.output_sep2)
            #genutils.Term.cout.flush()



