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

import sys
import StringIO
import textwrap

from wx.py.buffer import Buffer
import wx.py.dispatcher
from wx.py import editwindow
import wx.py.frame
from wx.py.pseudo import PseudoFileIn
from wx.py.pseudo import PseudoFileOut
from wx.py.pseudo import PseudoFileErr
#from wx.py.version import VERSION

from IPython import Shell
from notabene import notebook

from lxml import etree

def findnew(element, tag):
    """Tries to find the tag in the element. If there is no such element,
    creates one"""
    el = element.find(tag)
    if el is None:
        el = etree.SubElement(element, tag)
    return el

class IPythonLog(object):
    def __init__(self, doc, notebook, logid, *args, **kwds):
        self.doc = doc
        self.notebook = notebook
        self.log = notebook.get_log(logid)
        self.logid = logid
        self.lastrun = -1 #the last input that is run
        self.last = False
        #Here I will sort the cells, according to their numbers
        self.log[:] = sorted(self.log, key = lambda x:int(x.attrib['number']))
        #Append the empty element at the end
        self.SetLastInput()
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
        self.interp = Shell.IPShellGUI(argv=['-colors','NoColor'], user_ns=user_ns)
        self.excepthook_IP = sys.excepthook
        sys.excepthook = self.excepthook_orig
        del __builtin__

        #set up wrapper to use for long output
        self.wrapper = textwrap.TextWrapper()
        #end shell initialization
    
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
            del(self.log[-1])
            self.last = False
    
    def LastCell(self):
        """Return the last number of the last cell"""
        if self.last:
            return notebook.Cell(self.log[-1])
        else:
            
            raise Exception, "SetLastInput not called"
    lastcell = property(fget = LastCell)
            
    #TODO: I should support interactive input. Fix this.
    def readline(self, size):
        return ""
    def readlines(self, sizehint):
        return ""
    def raw_input(self, prompt = None):
        return ""
    
    def writeOut(self, text):
        """Write to the output of the current cell"""
        
        elem = self.log[-1] # we always process the last cell
        se = elem.find('stdout')
        if se is None:
            se = etree.SubElement(elem, 'stdout')
            se.text = ""
        se.text = se.text + text
        #TODO: Update the view

    def writeErr(self, text):
        elem = self.log[-1]
        se = elem.find('stderr')
        if se is None:
            se = etree.SubElement(elem, 'stderr')
            se.text = ""
        se.text = se.text + text
        #TODO: Update the view

    
    def Append(self, input, output = None, number = 0):
        """Adds a new cell with the given input at the end of the list.
        Returns the cell. Number is used only if the log is empty."""
        l = len(self.log)
        if l != 0 :
            number = int(self.log[-1].attrib['number'])+1
        elem = etree.Element('cell', number=str(number))
        self.log.append(elem)
        se = etree.SubElement(elem, 'input')
        se.text = str(input)
        if output is not None:
            se = etree.SubElement(elem, 'output')
            se.text = str(output)
        return notebook.Cell(elem)
    
    def Clear(self):
        
        self.log.clear()
        self.__reset()
        
    def Get(self, number): #TODO: this method is slow, so don't use it
        """Returns the cell with the given number"""
        return notebook.Cell(self.notebook.get_cell(number = number, logid = self.logid))
    
    
    #def Set(self, id, input, output = None):
    #    self.log[id] = [input, output]
        
    def Run(self, number = None):
        """ This method will run the code in all cells with numbers larger or
        equal to number. If number is None it will run only the last cell.
        Internally it uses __run. Returns True, if the input is processed,
        False if it needs more input."""
        
        if number == None:
            return self.__run(notebook.Cell(self.log[-1]))
        expr = '//cell[@number>=%d]'%(number,)
        print expr #dbg
        cells = sorted((notebook.Cell(x) for x in self.log.xpath(expr)), key =
                       lambda x:x.number)
                
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
        print 'running code...'
        print 'input-> ',cell.input
        self.output = findnew(cell.element, 'output')
        self.stdout = findnew(cell.element, 'stdout')
        self.stderr = findnew(cell.element, 'stderr')
        self.output.text = ''
        self.stdout.text = ''
        self.stderr.text = ''
        
        cout = StringIO.StringIO()
        cerr = StringIO.StringIO()
        #The first and last characters of cell.input are '\n'
        retval = self.interp.runlines(cell.input[1:-1],\
                                      displayhook = self.displayhook,\
                                      stdout = cout, stderr = cerr)
        #Retrieve stdout
        text = '\n' + cout.getvalue()
        print 'unformatted stdout ->', text
        if text != '\n':
            if text[-1] != '\n':
                text = text + '\n'
            self.stdout.text = text
        cout.close()
        
        #Retrieve stderr
        text = '\n' + cerr.getvalue()
        print 'unformatted stderr ->', text
        if text != '\n':
            if text[-1] != '\n':
                text = text + '\n'
            self.stderr.text = text
        cerr.close()
        
        print 'output ->', self.output.text #dbg
        print 'stdout ->', self.stdout.text #dbg
        print 'stderr ->', self.stderr.text #dbg
        if self.output.text is None:
            cell.element.remove(self.output)
        else:
            self.output.text = self.wrapper.fill(self.output.text) + '\n'#wrap the output
            print 'wrapped output ->', self.output.text #dbg
        del self.output
        if self.stdout.text is None:
            cell.element.remove(self.stdout)
        del self.stdout
        if self.stderr.text is None:
            cell.element.remove(self.stderr)
        del self.stderr
        
        #TODO: the return value of runlines should match the return value of __run
        if retval: 
            return False
        else:
            return True
    
    def displayhook(self, obj):
        print >> self.stdout_orig,  'displayhook called' #dbg
        # We want to keep only the last output
        self.output.text = '\n' + str(obj) + '\n'
