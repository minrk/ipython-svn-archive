""" IPythonLog.py Contains a IPythonLog class which holds the information of one log"""

import sys

from wx.py.buffer import Buffer
import wx.py.dispatcher
from wx.py import editwindow
import wx.py.frame
from wx.py.pseudo import PseudoFileIn
from wx.py.pseudo import PseudoFileOut
from wx.py.pseudo import PseudoFileErr
from wx.py.version import VERSION

class IPythonLog:
    def __init__(self, logid = "default-log", *args, **kwds):
        self.log = list()
        self.logid = logid
        self.lastrun = -1 #the last input that is run
        
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
        id = self.currentid #this is set by __run to know which line we are processing
        if self.log[id][1] is None:
            self.log[id][1] = text
        else:
            self.log[id][1].append(text)
        #TODO: Update the view

    def writeErr(self, text):
        id = self.currentid #this is set by __run to know which line we are processing
        if self.log[id][1] is None:
            self.log[id][1] = text
        else:
            self.log[id][1].append(text)
        #TODO: Update the view

    
    def Append(self, input, output = None):
        """Adds a new input at the end of the list. Returns the index"""
        self.log.append([input, output])
        return len(self.log)-1
    
    def Clear(self):
        self.log = list()
        self.__reset()
        
    def Get(self, id):
        return self.log[id]
    
    def Set(self, id, input, output = None):
        self.log[id] = [input, output]
        
    def Run(self, id):
        """ this method must run the code with the given number through the
        interpreter. It must also rerun any other parts of the log if
        needed. Internally it uses __run. Returns True, if the input is processed, False if
        it needs more input."""
        
        if id > self.lastrun:
            for idd in range(self.lastrun+1, id+1):
                if not self.__run(idd):
                    self.lastrun = idd-1
                    return False
            self.lastrun = id
        else: #We should start from the beginning here
            self.__reset()
            for idd in range(0, id+1):
                if not self.__run(idd):
                    self.lastrun = idd-1
                    return False
            self.lastrun - id
        return True
    
    def __reset(self):
        """ Resets the interpreter, namespace etc """
        pass
    
    def __run(self, id):
        """ This methods runs the input lines. """
        self.log[id][1] = "out: " + self.log[id][0] #TODO: fix this
        return True
