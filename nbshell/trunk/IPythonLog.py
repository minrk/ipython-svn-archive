""" IPythonLog.py Contains a IPythonLog class which holds the information of one log"""

import sys

from wx.py.buffer import Buffer
import wx.py.dispatcher
from wx.py import editwindow
import wx.py.frame
from wx.py.pseudo import PseudoFileIn
from wx.py.pseudo import PseudoFileOut
from wx.py.pseudo import PseudoFileErr
#from wx.py.version import VERSION

from notabene import notebook

from lxml import etree
class IPythonLog(object):
    def __init__(self, doc, notebook, logid, *args, **kwds):
        self.doc = doc
        self.notebook = notebook
        self.log = notebook.get_log(logid)
        self.logid = logid
        self.lastrun = -1 #the last input that is run
        #Here I will sort the cells, according to their numbers
        tmp = [(int(x.attrib['number']), x) for x in self.log]
        def cmpfunc(a,b):
            return cmp(a[0], b[0])
        tmp.sort(cmpfunc)
        self.log[:] = [x[1] for x in tmp]
        #set up the interpreter. We use the PyCrust interpreter for now
        self.locals = {}
        # Grab these so they can be restored by self.redirect* methods.
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        # Import a default interpreter class if one isn't provided.
        from wx.py.interpreter import Interpreter
        # Create a replacement for stdin.
        self.reader = PseudoFileIn(self.readline, self.readlines)
        self.reader.input = ''
        self.reader.isreading = False
        # Set up the interpreter.
        self.interp = Interpreter(locals=locals,
                                  rawin=self.raw_input,
                                  stdin=self.reader,
                                  stdout=PseudoFileOut(self.writeOut),
                                  stderr=PseudoFileErr(self.writeErr),
                                  *args, **kwds)
        
        import __builtin__
        __builtin__.close = __builtin__.exit = __builtin__.quit = \
                   'Click on the close button to leave the application.'
        del __builtin__

        #end shell initialization
        
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
            number = int(self.log[l-1].attrib['number'])+1
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
        
        cells = sorted((Cell(x) for x in self.log.xpath('\\cell[@number>=%d'%(number,))), key = lambda x:x.number)
                
        for cell in cells:
            if not self.__run(cell):
                return False
        return True

    def __reset(self):
        """ Resets the interpreter, namespace etc """
        pass
    
    def __run(self, cell):
        """ This methods runs the input lines. """
        output = cell.element.find('output')
        if output is None:
            output = etree.SubElement(cell.element, 'output')
        output.text = '\nout: ' + cell.input #TODO: fix this
        return True
