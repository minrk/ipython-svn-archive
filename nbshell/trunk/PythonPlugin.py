import os
import sys

import wx
from wx import stc
from wx import py

from wx.py.buffer import Buffer
import wx.py.dispatcher
from wx.py import editwindow
import wx.py.frame
from wx.py.pseudo import PseudoFileIn
from wx.py.pseudo import PseudoFileOut
from wx.py.pseudo import PseudoFileErr
from wx.py.version import VERSION

NAVKEYS = (wx.WXK_END, wx.WXK_LEFT, wx.WXK_RIGHT,
           wx.WXK_UP, wx.WXK_DOWN, wx.WXK_PRIOR, wx.WXK_NEXT)

def ifelse(a,b,c):
    if (a):
        return b
    else:
        return c

def GetPluginFactory():
    """ Returns the factory object for the plugin. This function is called
    at the start of the program and should be called only once.
    """
    return PythonPluginFactory()

class PythonPluginFactory:
    """ This class is responsible for creating the document and view parts of 
    a plugin. Also it has some functions giving information about the plugin.
    The reason this class exists is because the document and view classes of
    the program shouldn't care how plugin objects are created. For example all
    the plain text in the notebook could be contained a single object which is 
    returned every time the document class wants to get a new one."""
    
    def GetString(self):
        """ Returns the type string of the plugin. This is used when a notebook
        file is loaded. See notebookformat.txt for more info"""
        return "python"
    
    def GetType(self):
        """ Returns the way data should be passed to the plugin. Currently
        supported types are "raw" and "encoded". See notebookformat.txt for 
        more info"""
        return "raw" #Probably only the python code plugin should be raw
        
    def CreateDocumentPlugin(self,document, data=None):
        """Creates the document part of the plugin. The returned object is 
        stored in ipgDocument.celllist and is responsible for storing and
        serialization of data. "data" contains initial data for the plugin.
        """
        return PythonDocumentPlugin(document, data)
    
    def CreateViewPlugin(self,docplugin, view):
        """ Creates a view plugin connected to the given document plugin and 
        the given view. The view plugin is responsible for creating windows,
        handling events, etc. In simple plugins the document and the view plugin
        may be the same object
        """
        
        #In the distant future I might need to create views of different type for
        #one doc plugin. For example for a LaTeX plugin I might create a view 
        #for previewing in the notebook widget and a view for editing the LaTeX
        #code in a separate window
        if view.type=="notebook":
            return PythonNotebookViewPlugin(docplugin, view)
        else:
            return None #Well here I should throw an exception, however I am 
                        #not supposed to get to this line for a long long time
#end GenericPluginFactory

class PythonDocumentPlugin:
    def __init__(self, document, data=None, log = "default-log"):
        """Initialization"""
        self.document = document
        self.log = self.document.logs[log]
        self.index = None   #Set by AddCell, InsertCell, DeleteCell
        self.view = None    #This plugin is designed for a single view. For
                            #multiple views there should be some modifications
        
        self.data = [] # this is a list of tuples of the form (id, type), where the
                       # tuple (id, type) corresponds to self.log.Get(id)[type]
        #self.LoadData(data)



    def Clear(self):
        """Clears all data"""
        self.data = []
        self.view.Update()
        
    
    def LoadData(self, data=None):
        """Loads data in the object. If "data" is None then clears all data"""
        return #well we do nothing here
        #There is a philosophical problem with Scintilla here. All its 
        #functionality is in the widget object. They do not have an object of
        #a separate type handling data. Well, they actually do, but it can do
        #nothing with the data it conatains. So that's why when the view is
        #created it will add a member self.data which is simply a reference
        #to the Scintilla widget. And I will pretend, that I don't know this
        #and will only use its functionality for handling data.
        if (self.view is None):
            self.text = data #here self.data is not yet created
        else:
            if data is None:
                self.data.ClearAll()
            else:
                self.data.SetText(data)
            self.view.Update()

    def LoadEncoded(self, itr, args):
        
        self.Clear()
        if self.view is None:
            for line in itr:
                self.text = self.text+line
        else:
            for line in itr:
                self.data.AddText(line)
        self.view.Update()

    def GetArgs(self):
        return ("python",)
    
    def Serialize(self, file=None, encodefunc = None):
        """Stores data in file. If the type of the plugin is raw, then
        the "file" parameter contains a file object where data should be
        written. If the type is encoded then the encodefunc parameter contains
        a function which should be called for each line of text which should 
        be serialized
        """
        #Here I assume that noone uses the document plugin without creating a
        #view plugin, which initializes self.data
        #TODO: fix it someday (yeah right :)
        linecnt = self.data.GetLineCount()
        [encodefunc(self.data.GetLine(x)) for x in range(0, linecnt-1)]
    
    def SetView(self, view):
        """Set the view for the plugin"""
        self.view=view
    
    def GetViewPlugin(self, view):
        return self.view

    def GetFactory(self):
        return PlainTextPluginFactory()

class PythonNotebookViewPlugin:
    def __init__(self, docplugin, view):
        """Initialization"""
        self.view = view
        self.doc = docplugin
        self.document=docplugin.document
        self.doc.SetView(self)
        self.window = None
        self.document = docplugin.document

    def GetFirstId(self):
        """ This view is responsible for a list of consequent windows in the
        #notebook widget. GetFirsId returns the id of the first window"""
        return self.id
        
    def GetLastId(self):
        """See the description of GetFirstId"""
        return self.id
        
    def Update(self):
        """ This method is required for all view implementations. It must
        update the view plugin.
        
        Remark: In order to update the view you must also call the Update
        method of the view after you call the Update method of the view 
        plugin. This is made so for efficiency. For example In the notebook
        view when you update a document cell you will probably need to call 
        RelayoutCells. So if you call Update on each document cell and call 
        RelayoutCells in each update this would be really inefficient.
        """
        if self.window is None: #then this is the first time Update is called
            #1. Create the window and set the document plugin
            self.window = Shell(self, self.view, -1)
            print "getting id"
            self.id = self.window.GetId()
            print "id:", self.id
            self.window.view = self
            #2. Add the window at the correct place in the notebook widget
            if self.doc.index == 0: #put the window at the beginning of the document
                print "inserting cell"
                self.view.InsertCell(self.window, 0, update=False)
            else:
                print "adding cell"
                prevcell = self.document.GetCell(self.doc.index-1)
                viewplugin = prevcell.GetViewPlugin(self.view)
                print self.doc.index
                print viewplugin
                lastid = viewplugin.GetLastId()
                print lastid
                index = self.view.GetIndex(lastid)+1
                self.view.InsertCell(self.window, index, update = False)
        # Set the text in the window
        #TODO: It is really stupid to rewrite the text for 
        #every little change that can occur. Think of a way not to avoid this
        data = self.doc.data
        print "data->", data
        
        log = self.doc.log
        print "log->", log.log
        self.window.ClearAll()
        self.window.line2log = []
        for i in range(len(data)):
            id, type = data[i]
            text = log.Get(id)[type]
            linestart = self.window.GetLineCount()
            self.window.AddText(((type and "Out[") or "In[") + str(id) + "] " + text)
            lineend =  self.window.GetLineCount()
            for j in range(linestart, lineend):
                self.window.line2log.append((i, j - linestart))
                #print "i -> %s, id->%s, type->%s, text->%s"%(str(i), str(id), str(type), str(text))



    def Close(self, update = True):
        index = self.view.GetIndex(self.id)
        self.view.DeleteCell(index, update)

class ShellFacade:
    """Simplified interface to all shell-related functionality.

    This is a semi-transparent facade, in that all attributes of other
    are accessible, even though only some are visible to the user."""

    name = 'Shell Interface'
#    revision = __revision__ #TODO: fix

    def __init__(self, other):
        """Create a ShellFacade instance."""
        d = self.__dict__
        d['other'] = other
        d['helpText'] = \
"""
* Key bindings:
Home              Go to the beginning of the command or line.
Shift+Home        Select to the beginning of the command or line.
Shift+End         Select to the end of the line.
End               Go to the end of the line.
Ctrl+C            Copy selected text, removing prompts.
Ctrl+Shift+C      Copy selected text, retaining prompts.
Ctrl+X            Cut selected text.
Ctrl+V            Paste from clipboard.
Ctrl+Shift+V      Paste and run multiple commands from clipboard.
Ctrl+Up Arrow     Retrieve Previous History item.
Alt+P             Retrieve Previous History item.
Ctrl+Down Arrow   Retrieve Next History item.
Alt+N             Retrieve Next History item.
Shift+Up Arrow    Insert Previous History item.
Shift+Down Arrow  Insert Next History item.
F8                Command-completion of History item.
                  (Type a few characters of a previous command and press F8.)
Ctrl+Enter        Insert new line into multiline command.
Ctrl+]            Increase font size.
Ctrl+[            Decrease font size.
Ctrl+=            Default font size.
"""

    def help(self):
        """Display some useful information about how to use the shell."""
        self.write(self.helpText)

    def __getattr__(self, name):
        if hasattr(self.other, name):
            return getattr(self.other, name)
        else:
            raise AttributeError, name

    def __setattr__(self, name, value):
        if self.__dict__.has_key(name):
            self.__dict__[name] = value
        elif hasattr(self.other, name):
            setattr(self.other, name, value)
        else:
            raise AttributeError, name

    def _getAttributeNames(self):
        """Return list of magic attributes to extend introspection."""
        list = [
            'about',
            'ask',
            'autoCallTip',
            'autoComplete',
            'autoCompleteCaseInsensitive',
            'autoCompleteIncludeDouble',
            'autoCompleteIncludeMagic',
            'autoCompleteIncludeSingle',
            'clear',
            'pause',
            'prompt',
            'quit',
            'redirectStderr',
            'redirectStdin',
            'redirectStdout',
            'run',
            'runfile',
            'wrap',
            'zoom',
            ]
        list.sort()
        return list


class Shell(editwindow.EditWindow):
    """Shell based on StyledTextCtrl."""

    name = 'Shell'
    #revision = __revision__ #TODO: fix

    def __init__(self,view, parent, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.CLIP_CHILDREN):
        """Create Shell instance."""
        editwindow.EditWindow.__init__(self, parent, id, pos, size, style)

        self.id = self.GetId()
        self.parent = parent
        self.view = view
        self.document = view.doc
        self.log = self.document.log
        self.line2log = [] # For each line in the window contains a tuple of
                           # the id of the corresponding part of the document and
                           # the corresponding line in the text in the log
                           #
                           # (id, n) -> the n'th line of document.data[id] 
        
        self.oldlineno = 1 # used by OnModified. Is there a way to
                           # declare this inside the method? Like a
                           # C++ static variable
        self.oldpos = (0,0)

        self.wrap()

        # Find out for which keycodes the interpreter will autocomplete.
        self.autoCompleteKeys = self.document.log.interp.getAutoCompleteKeys()
        # Keep track of the last non-continuation prompt positions.
        #self.promptPosStart = 0
        self.promptPosEnd = 0
        # Keep track of multi-line commands.
        self.more = False
        # Create the command history.  Commands are added into the
        # front of the list (ie. at index 0) as they are entered.
        # self.historyIndex is the current position in the history; it
        # gets incremented as you retrieve the previous command,
        # decremented as you retrieve the next, and reset when you hit
        # Enter.  self.historyIndex == -1 means you're on the current
        # command, not in the history.
        #self.history = []
        #self.historyIndex = -1
        # Assign handlers for keyboard events.
        wx.EVT_CHAR(self, self.OnChar)
        wx.EVT_KEY_DOWN(self, self.OnKeyDown)
        # Assign handler for idle time.
        self.waiting = False
        wx.EVT_IDLE(self, self.OnIdle)
        stc.EVT_STC_MODIFIED(self, id, self.OnModified)
        stc.EVT_STC_UPDATEUI(self, id, self.OnUpdateUI)
        # Display the introductory banner information.
        #self.showIntro(introText) #TODO: remove this
        # Assign some pseudo keywords to the interpreter's namespace.
        #self.setBuiltinKeywords() #TODO move in the view
        # Add 'shell' to the interpreter's local namespace.
        #self.setLocalShell()
        # Do this last so the user has complete control over their
        # environment.  They can override anything they want.
        #self.execStartupScript(self.interp.startupScript) #TODO: what does this button do?
        #wx.CallAfter(self.ScrollToLine, 0)

    def Resize (self, width = None):
        """ See StaticTextPlugin.Resize """
        if width is None:
            width = self.GetClientSizeTuple()[0]

        height = self.TextHeight(0)*self.GetLineCount() #works, because all lines have the same height
        self.SetClientSizeWH(width, height)

    def SetTheFocus(self, pos, start):
        """ Sets the focus to this cell """
        self.SetFocus()
        pos1 = tuple(self.PointFromPosition(self.GetCurrentPos()))
        self.parent.ScrollTo(self.view.doc.index, pos1) # show the highest pixel of the caret
        if start: #The focus came from the previous cell
            self.GotoPos(min(pos, self.GetLineEndPosition(0)))
        else: #The focus came from the next cell
            lastline = self.GetLineCount() - 1
            self.GotoPos(min(self.PositionFromLine(lastline) + pos, self.GetLineEndPosition(lastline)))
    
    def OnModified (self, evt):
        lineno = self.GetLineCount()
        if self.oldlineno != lineno :
            self.oldlineno = lineno
            self.parent.RelayoutCells(id = self.id)

    def OnUpdateUI (self, evt):
        editwindow.EditWindow.OnUpdateUI(self, evt)
        pos = tuple(self.PointFromPosition(self.GetCurrentPos()))
        if (pos != self.oldpos):
            self.parent.ScrollTo(self.view.doc.index, pos) # show the highest pixel of the caret
#            self.view.ScrollTo(self.cell.index, (pos[0], pos[1]+self.TextHeight(0))) # now show the lowest pixel.
            #TODO: If there is a way to make scrolling slower, I can't
            #think of it right now :)
            self.oldpos = pos

#    def destroy(self):
#        del self.interp

    def setFocus(self):
        """Set focus to the shell."""
        self.SetFocus()

    def OnIdle(self, event):
        """Free the CPU to do other things."""
        if self.waiting:
            time.sleep(0.05)
        event.Skip()

#    def showIntro(self, text=''):
#        """Display introductory text in the shell."""
#        if text:
#            if not text.endswith(os.linesep):
#                text += os.linesep
#            self.write(text)
#        try:
#            self.write(self.interp.introText)
#        except AttributeError:
#            pass

#TODO: Move this somewhere
#    def setBuiltinKeywords(self):
#        """Create pseudo keywords as part of builtins.
#
#        This sets `close`, `exit` and `quit` to a helpful string.
#        """
#        import __builtin__
#        __builtin__.close = __builtin__.exit = __builtin__.quit = \
#            'Click on the close button to leave the application.'

    def quit(self):
        """Quit the application."""

        # XXX Good enough for now but later we want to send a close event.

        # In the close event handler we can make sure they want to
        # quit.  Other applications, like PythonCard, may choose to
        # hide rather than quit so we should just post the event and
        # let the surrounding app decide what it wants to do.
        self.write('Click on the close button to leave the application.')

#    def setLocalShell(self):
#        """Add 'shell' to locals as reference to ShellFacade instance."""
#        self.interp.locals['shell'] = ShellFacade(other=self)

#TODO: Maybe I need this somewhere
#    def execStartupScript(self, startupScript):
#       """Execute the user's PYTHONSTARTUP script if they have one."""
#        if startupScript and os.path.isfile(startupScript):
#            text = 'Startup script executed: ' + startupScript
#            self.push('print %r; execfile(%r)' % (text, startupScript))
#        else:
#            self.push('')

#TODO: Make an about dialog and mention PyCrust there
#    def about(self):
#        """Display information about Py."""
#        text = """
#Author: %r
#Py Version: %s
#Py Shell Revision: %s
#Py Interpreter Revision: %s
#Python Version: %s
#wxPython Version: %s
#Platform: %s""" % \
#        (__author__, VERSION, self.revision, self.interp.revision,
#         sys.version.split()[0], wx.VERSION_STRING, sys.platform)
#        self.write(text.strip())

    def OnChar(self, event):
        """Keypress event handler.

        Only receives an event if OnKeyDown calls event.Skip() for the
        corresponding event."""

        # Prevent modification of previously submitted
        # commands/responses.
        if not self.CanEdit():
            return
        key = event.KeyCode()
        currpos = self.GetCurrentPos()
        stoppos = self.promptPosEnd
        # Return (Enter) needs to be ignored in this handler.
        if key == wx.WXK_RETURN:
            pass
        elif key in self.autoCompleteKeys:
            # Usually the dot (period) key activates auto completion.
            # Get the command between the prompt and the cursor.  Add
            # the autocomplete character to the end of the command.
            if self.AutoCompActive():
                self.AutoCompCancel()
            command = self.GetTextRange(stoppos, currpos) + chr(key)
            self.write(chr(key))
            if self.autoComplete:
                self.autoCompleteShow(command)
        elif key == ord('('):
            # The left paren activates a call tip and cancels an
            # active auto completion.
            if self.AutoCompActive():
                self.AutoCompCancel()
            # Get the command between the prompt and the cursor.  Add
            # the '(' to the end of the command.
            self.ReplaceSelection('')
            command = self.GetTextRange(stoppos, currpos) + '('
            self.write('(')
            self.autoCallTipShow(command)
        else:
            # Allow the normal event handling to take place.
            event.Skip()

    def OnKeyDown(self, event):
        """Key down event handler."""

        key = event.KeyCode()
        # If the auto-complete window is up let it do its thing.
        if self.AutoCompActive():
            event.Skip()
            return
        # Prevent modification of previously submitted
        # commands/responses.
        controlDown = event.ControlDown()
        altDown = event.AltDown()
        shiftDown = event.ShiftDown()
        currpos = self.GetCurrentPos()
        endpos = self.GetTextLength()
        selecting = self.GetSelectionStart() != self.GetSelectionEnd()
        # Return (Enter) is used to submit a command to the
        # interpreter.
        if not controlDown and key == wx.WXK_RETURN:
            if self.CallTipActive():
                self.CallTipCancel()
            self.processLine()
        # Ctrl+Return (Cntrl+Enter) is used to insert a line break.
        #elif controlDown and key == wx.WXK_RETURN:
        #    if self.CallTipActive():
        #        self.CallTipCancel()
        #    if currpos == endpos:
        #        self.processLine()
        #    else:
        #        self.insertLineBreak()
        # Let Ctrl-Alt-* get handled normally.
        elif controlDown and altDown:
            event.Skip()
        # Clear the current, unexecuted command.
        elif key == wx.WXK_ESCAPE:
            if self.CallTipActive():
                event.Skip()
        #    else:
        #        self.clearCommand()
        # Increase font size.
        elif controlDown and key in (ord(']'),):
            dispatcher.send(signal='FontIncrease')
        # Decrease font size.
        elif controlDown and key in (ord('['),):
            dispatcher.send(signal='FontDecrease')
        # Default font size.
        elif controlDown and key in (ord('='),):
            dispatcher.send(signal='FontDefault')
        # Cut to the clipboard.
        #elif (controlDown and key in (ord('X'), ord('x'))) \
        #or (shiftDown and key == wx.WXK_DELETE):
        #    self.Cut()
        # Copy to the clipboard.
        elif controlDown and not shiftDown \
            and key in (ord('C'), ord('c'), wx.WXK_INSERT):
            self.Copy()
        # Copy to the clipboard, including prompts.
        elif controlDown and shiftDown \
            and key in (ord('C'), ord('c'), wx.WXK_INSERT):
            self.CopyWithPrompts()
        # Copy to the clipboard, including prefixed prompts.
        elif altDown and not controlDown \
            and key in (ord('C'), ord('c'), wx.WXK_INSERT):
            self.CopyWithPromptsPrefixed()
        # Home needs to be aware of the prompt.
        #elif key == wx.WXK_HOME:
        #    home = self.promptPosEnd
        #    if currpos > home:
        #        self.SetCurrentPos(home)
        #        if not selecting and not shiftDown:
        #            self.SetAnchor(home)
        #            self.EnsureCaretVisible()
        #    else:
        #        event.Skip()
        #
        # The following handlers modify text, so we need to see if
        # there is a selection that includes text prior to the prompt.
        #
        # Don't modify a selection with text prior to the prompt.
        elif selecting and key not in NAVKEYS and not self.CanEdit():
            pass
        # Paste from the clipboard.
        #elif (controlDown and not shiftDown and key in (ord('V'), ord('v'))) \
        #         or (shiftDown and not controlDown and key == wx.WXK_INSERT):
        #    self.Paste()
        # Paste from the clipboard, run commands.
        #elif controlDown and shiftDown and key in (ord('V'), ord('v')):
        #    self.PasteAndRun()
        # Replace with the previous command from the history buffer.
        #elif (controlDown and key == wx.WXK_UP) \
        #         or (altDown and key in (ord('P'), ord('p'))):
        #    self.OnHistoryReplace(step=+1)
        # Replace with the next command from the history buffer.
        #elif (controlDown and key == wx.WXK_DOWN) \
        #         or (altDown and key in (ord('N'), ord('n'))):
        #    self.OnHistoryReplace(step=-1)
        # Insert the previous command from the history buffer.
        #elif (shiftDown and key == wx.WXK_UP) and self.CanEdit():
        #    self.OnHistoryInsert(step=+1)
        # Insert the next command from the history buffer.
        #elif (shiftDown and key == wx.WXK_DOWN) and self.CanEdit():
        #    self.OnHistoryInsert(step=-1)
        # Search up the history for the text in front of the cursor.
        #elif key == wx.WXK_F8:
        #    self.OnHistorySearch()
        # Don't backspace over the latest non-continuation prompt.
        #elif key == wx.WXK_BACK:
        #    if selecting and self.CanEdit():
        #        event.Skip()
        #    elif currpos > self.promptPosEnd:
        #        event.Skip()
        # Only allow these keys after the latest prompt.
        elif key in (wx.WXK_TAB, wx.WXK_DELETE):
            if self.CanEdit():
                event.Skip()
        # Don't toggle between insert mode and overwrite mode.
        elif key == wx.WXK_INSERT:
            pass
        # Don't allow line deletion.
        elif controlDown and key in (ord('L'), ord('l')):
            pass
        # Don't allow line transposition.
        elif controlDown and key in (ord('T'), ord('t')):
            pass
        # Basic navigation keys should work anywhere.
        elif key in NAVKEYS:
            event.Skip()
        # Protect the readonly portion of the shell.
        elif not self.CanEdit():
            pass
        else:
            event.Skip()

    def clearCommand(self):
        """Delete the current, unexecuted command."""
        startpos = self.promptPosEnd
        endpos = self.GetTextLength()
        self.SetSelection(startpos, endpos)
        self.ReplaceSelection('')
        self.more = False

    def OnHistoryReplace(self, step):
        """Replace with the previous/next command from the history buffer."""
        self.clearCommand()
        self.replaceFromHistory(step)

    def replaceFromHistory(self, step):
        """Replace selection with command from the history buffer."""
        ps2 = str(sys.ps2)
        self.ReplaceSelection('')
        newindex = self.historyIndex + step
        if -1 <= newindex <= len(self.history):
            self.historyIndex = newindex
        if 0 <= newindex <= len(self.history)-1:
            command = self.history[self.historyIndex]
            command = command.replace('\n', os.linesep + ps2)
            self.ReplaceSelection(command)

    def OnHistoryInsert(self, step):
        """Insert the previous/next command from the history buffer."""
        if not self.CanEdit():
            return
        startpos = self.GetCurrentPos()
        self.replaceFromHistory(step)
        endpos = self.GetCurrentPos()
        self.SetSelection(endpos, startpos)

    def OnHistorySearch(self):
        """Search up the history buffer for the text in front of the cursor."""
        if not self.CanEdit():
            return
        startpos = self.GetCurrentPos()
        # The text up to the cursor is what we search for.
        numCharsAfterCursor = self.GetTextLength() - startpos
        searchText = self.getCommand(rstrip=False)
        if numCharsAfterCursor > 0:
            searchText = searchText[:-numCharsAfterCursor]
        if not searchText:
            return
        # Search upwards from the current history position and loop
        # back to the beginning if we don't find anything.
        if (self.historyIndex <= -1) \
        or (self.historyIndex >= len(self.history)-2):
            searchOrder = range(len(self.history))
        else:
            searchOrder = range(self.historyIndex+1, len(self.history)) + \
                          range(self.historyIndex)
        for i in searchOrder:
            command = self.history[i]
            if command[:len(searchText)] == searchText:
                # Replace the current selection with the one we found.
                self.ReplaceSelection(command[len(searchText):])
                endpos = self.GetCurrentPos()
                self.SetSelection(endpos, startpos)
                # We've now warped into middle of the history.
                self.historyIndex = i
                break

    def setStatusText(self, text):
        """Display status information."""

        # This method will likely be replaced by the enclosing app to
        # do something more interesting, like write to a status bar.
        print text

    def insertLineBreak(self):
        """Insert a new line break."""
        if self.CanEdit():
            self.write(os.linesep)
            self.more = True
            self.prompt()

    def updateLog(self):
        """Updates the log to the current text in the widget. This method is
        run whenever the user presses Enter"""
        
        for (id, type) in self.document.data:
            self.log.Get(id)[type] = None
        
        for i in range(len(self.line2log)):
            doc_id, line = self.line2log[i]
            id, type = self.document.data[doc_id]
            element = self.log.Get(id)
            promptlen = self.promptLen(i)
            if element[type] is None:
                
                element[type] = self.GetLine(i)[promptlen:]
            else:
                element[type] = element[type]+self.GetLine(i)[promptlen:]

    def promptLen(self, linenum):
        """Returns the lenght of the prompt that is on the given line. Used
        only for input prompts."""
        
        #get the number of digits of the number of the input
        doc_id = self.line2log[linenum][0]
        id, type = self.document.data[doc_id]
        print "promptLen: linenum->%d, doc_id->%d, id->%d, type->%d"%(linenum, doc_id, id, type)
        return len(str(id))+(type and 6 or 5)
    
    def processLine(self):
        """Process the line of text at which the user hit Enter."""
        #Update the log
        self.updateLog()
        linenum = self.GetCurrentLine()
        print "linenum->", linenum
        item = self.line2log[linenum]
        doc_id = item[0]
        id, type = self.document.data[doc_id]
        line = item[1]
        print "(doc_id, id, type, line)->", (doc_id, id, type, line)
        if type == 1: #this is output, so we do nothing
            return

        #try to run the current input. If it needs more, insert a line and continue editing
        if self.log.Run(id): # we have run the text and generated output
            if len(self.document.data) == doc_id+1: #this is the last cell so add the output after it
                self.document.data.append((id, 1))
                #append a new cell
                id1 = self.log.Append("\n") #all input and output strings must finish in '\n'
                self.document.data.append((id1, 0))
            elif self.document.data[doc_id+1] != (id, 1): #the next cell is not the output of this input
                self.document.data.insert(doc_id+1, (id, 1))
            self.view.Update()
        else: #We need more input, simply insert a line
            self.InsertText(self.GetLineEndPosition(linenum), "\n")
            self.line2log.append(None)
            for i in range(len(self.line2log)-1, linenum+1, -1):
                self.line2log[i] = self.line2log[i-1]
            self.line2log[linenum+1] = (item[0], item[1]+1)
            #here we don't need an update, I think
        #thepos = self.GetCurrentPos()
        #startpos = self.promptPosEnd
        #endpos = self.GetTextLength()
        #ps2 = str(sys.ps2)
        ## If they hit RETURN inside the current command, execute the
        ## command.
        #if self.CanEdit():
            #self.SetCurrentPos(endpos)
            #self.interp.more = False
            #command = self.GetTextRange(startpos, endpos)
            #lines = command.split(os.linesep + ps2)
            #lines = [line.rstrip() for line in lines]
            #command = '\n'.join(lines)
            #if self.reader.isreading:
                #if not command:
                    ## Match the behavior of the standard Python shell
                    ## when the user hits return without entering a
                    ## value.
                    #command = '\n'
                #self.reader.input = command
                #self.write(os.linesep)
            #else:
                #self.push(command)
        ## Or replace the current command with the other command.
        #else:
            ## If the line contains a command (even an invalid one).
            #if self.getCommand(rstrip=False):
                #command = self.getMultilineCommand()
                #self.clearCommand()
                #self.write(command)
            ## Otherwise, put the cursor back where we started.
            #else:
                #self.SetCurrentPos(thepos)
                #self.SetAnchor(thepos)

    def getMultilineCommand(self, rstrip=True):
        """Extract a multi-line command from the editor.

        The command may not necessarily be valid Python syntax."""
        # XXX Need to extract real prompts here. Need to keep track of
        # the prompt every time a command is issued.
        ps1 = str(sys.ps1)
        ps1size = len(ps1)
        ps2 = str(sys.ps2)
        ps2size = len(ps2)
        # This is a total hack job, but it works.
        text = self.GetCurLine()[0]
        line = self.GetCurrentLine()
        while text[:ps2size] == ps2 and line > 0:
            line -= 1
            self.GotoLine(line)
            text = self.GetCurLine()[0]
        if text[:ps1size] == ps1:
            line = self.GetCurrentLine()
            self.GotoLine(line)
            startpos = self.GetCurrentPos() + ps1size
            line += 1
            self.GotoLine(line)
            while self.GetCurLine()[0][:ps2size] == ps2:
                line += 1
                self.GotoLine(line)
            stoppos = self.GetCurrentPos()
            command = self.GetTextRange(startpos, stoppos)
            command = command.replace(os.linesep + ps2, '\n')
            command = command.rstrip()
            command = command.replace('\n', os.linesep + ps2)
        else:
            command = ''
        if rstrip:
            command = command.rstrip()
        return command

    def getCommand(self, text=None, rstrip=True):
        """Extract a command from text which may include a shell prompt.

        The command may not necessarily be valid Python syntax."""
        if not text:
            text = self.GetCurLine()[0]
        # Strip the prompt off the front leaving just the command.
        command = self.lstripPrompt(text)
        if command == text:
            command = ''  # Real commands have prompts.
        if rstrip:
            command = command.rstrip()
        return command

    def lstripPrompt(self, text):
        """Return text without a leading prompt."""
        ps1 = str(sys.ps1)
        ps1size = len(ps1)
        ps2 = str(sys.ps2)
        ps2size = len(ps2)
        # Strip the prompt off the front of text.
        if text[:ps1size] == ps1:
            text = text[ps1size:]
        elif text[:ps2size] == ps2:
            text = text[ps2size:]
        return text

    def push(self, command):
        """Send command to the interpreter for execution."""
        self.write(os.linesep)
        busy = wx.BusyCursor()
        self.waiting = True
        self.more = self.interp.push(command)
        self.waiting = False
        del busy
        if not self.more:
            self.addHistory(command.rstrip())
        self.prompt()

    def addHistory(self, command):
        """Add command to the command history."""
        # Reset the history position.
        self.historyIndex = -1
        # Insert this command into the history, unless it's a blank
        # line or the same as the last command.
        if command != '' \
        and (len(self.history) == 0 or command != self.history[0]):
            self.history.insert(0, command)

    def write(self, text):
        """Display text in the shell.

        Replace line endings with OS-specific endings."""
        text = self.fixLineEndings(text)
        self.AddText(text)
        self.EnsureCaretVisible()

    def fixLineEndings(self, text):
        """Return text with line endings replaced by OS-specific endings."""
        lines = text.split('\r\n')
        for l in range(len(lines)):
            chunks = lines[l].split('\r')
            for c in range(len(chunks)):
                chunks[c] = os.linesep.join(chunks[c].split('\n'))
            lines[l] = os.linesep.join(chunks)
        text = os.linesep.join(lines)
        return text

    def prompt(self):
        """Display proper prompt for the context: ps1, ps2 or ps3.

        If this is a continuation line, autoindent as necessary."""
        isreading = self.reader.isreading
        skip = False
        if isreading:
            prompt = str(sys.ps3)
        elif self.more:
            prompt = str(sys.ps2)
        else:
            prompt = str(sys.ps1)
        pos = self.GetCurLine()[1]
        if pos > 0:
            if isreading:
                skip = True
            else:
                self.write(os.linesep)
        if not self.more:
            self.promptPosStart = self.GetCurrentPos()
        if not skip:
            self.write(prompt)
        if not self.more:
            self.promptPosEnd = self.GetCurrentPos()
            # Keep the undo feature from undoing previous responses.
            self.EmptyUndoBuffer()
        # XXX Add some autoindent magic here if more.
        if self.more:
            self.write(' '*4)  # Temporary hack indentation.
        self.EnsureCaretVisible()
        self.ScrollToColumn(0)

    def readline(self):
        """Replacement for stdin.readline()."""
        input = ''
        reader = self.reader
        reader.isreading = True
        self.prompt()
        try:
            while not reader.input:
                wx.YieldIfNeeded()
            input = reader.input
        finally:
            reader.input = ''
            reader.isreading = False
        input = str(input)  # In case of Unicode.
        return input

    def readlines(self):
        """Replacement for stdin.readlines()."""
        lines = []
        while lines[-1:] != ['\n']:
            lines.append(self.readline())
        return lines

    def raw_input(self, prompt=''):
        """Return string based on user input."""
        if prompt:
            self.write(prompt)
        return self.readline()

    def ask(self, prompt='Please enter your response:'):
        """Get response from the user using a dialog box."""
        dialog = wx.TextEntryDialog(None, prompt,
                                    'Input Dialog (Raw)', '')
        try:
            if dialog.ShowModal() == wx.ID_OK:
                text = dialog.GetValue()
                return text
        finally:
            dialog.Destroy()
        return ''

    def pause(self):
        """Halt execution pending a response from the user."""
        self.ask('Press enter to continue:')

    def clear(self):
        """Delete all text from the shell."""
        self.ClearAll()

    def run(self, command, prompt=True, verbose=True):
        """Execute command as if it was typed in directly.
        >>> shell.run('print "this"')
        >>> print "this"
        this
        >>>
        """
        # Go to the very bottom of the text.
        endpos = self.GetTextLength()
        self.SetCurrentPos(endpos)
        command = command.rstrip()
        if prompt: self.prompt()
        if verbose: self.write(command)
        self.push(command)

    def runfile(self, filename):
        """Execute all commands in file as if they were typed into the
        shell."""
        file = open(filename)
        try:
            self.prompt()
            for command in file.readlines():
                if command[:6] == 'shell.':
                    # Run shell methods silently.
                    self.run(command, prompt=False, verbose=False)
                else:
                    self.run(command, prompt=False, verbose=True)
        finally:
            file.close()

    def autoCompleteShow(self, command):
        """Display auto-completion popup list."""
        list = self.log.interp.getAutoCompleteList(command,
                    includeMagic=self.autoCompleteIncludeMagic,
                    includeSingle=self.autoCompleteIncludeSingle,
                    includeDouble=self.autoCompleteIncludeDouble)
        if list:
            options = ' '.join(list)
            offset = 0
            self.AutoCompShow(offset, options)

    def autoCallTipShow(self, command):
        """Display argument spec and docstring in a popup window."""
        if self.CallTipActive():
            self.CallTipCancel()
        (name, argspec, tip) = self.interp.getCallTip(command)
        if tip:
            dispatcher.send(signal='Shell.calltip', sender=self, calltip=tip)
        if not self.autoCallTip:
            return
        if argspec:
            startpos = self.GetCurrentPos()
            self.write(argspec + ')')
            endpos = self.GetCurrentPos()
            self.SetSelection(endpos, startpos)
        if tip:
            curpos = self.GetCurrentPos()
            tippos = curpos - (len(name) + 1)
            fallback = curpos - self.GetColumn(curpos)
            # In case there isn't enough room, only go back to the
            # fallback.
            tippos = max(tippos, fallback)
            self.CallTipShow(tippos, tip)

    def writeOut(self, text):
        """Replacement for stdout."""
        self.write(text)

    def writeErr(self, text):
        """Replacement for stderr."""
        self.write(text)

    def redirectStdin(self, redirect=True):
        """If redirect is true then sys.stdin will come from the shell."""
        if redirect:
            sys.stdin = self.reader
        else:
            sys.stdin = self.stdin

    def redirectStdout(self, redirect=True):
        """If redirect is true then sys.stdout will go to the shell."""
        if redirect:
            sys.stdout = PseudoFileOut(self.writeOut)
        else:
            sys.stdout = self.stdout

    def redirectStderr(self, redirect=True):
        """If redirect is true then sys.stderr will go to the shell."""
        if redirect:
            sys.stderr = PseudoFileErr(self.writeErr)
        else:
            sys.stderr = self.stderr

    def CanCut(self):
        """Return true if text is selected and can be cut."""
        if self.GetSelectionStart() != self.GetSelectionEnd() \
               and self.GetSelectionStart() >= self.promptPosEnd \
               and self.GetSelectionEnd() >= self.promptPosEnd:
            return True
        else:
            return False

    def CanPaste(self):
        """Return true if a paste should succeed."""
        if self.CanEdit() and editwindow.EditWindow.CanPaste(self):
            return True
        else:
            return False

    def CanEdit(self):
        """Return true if editing should succeed."""
        #TODO: why we need to know anythong about the selection here
        #if self.GetSelectionStart() != self.GetSelectionEnd():
        #    if self.GetSelectionStart() >= self.promptPosEnd \
        #           and self.GetSelectionEnd() >= self.promptPosEnd:
        #        return True
        #    else:
        #        return False
        #else:
        #    return self.GetCurrentPos() >= self.promptPosEnd
        pos = self.GetCurrentPos()
        line = self.LineFromPosition(pos)
        startpos = self.PositionFromLine(line)
        print "pos->", pos, " line->", line, " startpos->", startpos
        if self.line2log[line][1] == 1: #this line is output
            print "line is output"
            return False
        else:
            promptlen = self.promptLen(line)
            print "line is input, promptlen->", promptlen
            if startpos+promptlen > pos:
                return False
            else:
                return True

    def Cut(self):
        """Remove selection and place it on the clipboard."""
        if self.CanCut() and self.CanCopy():
            if self.AutoCompActive():
                self.AutoCompCancel()
            if self.CallTipActive():
                self.CallTipCancel()
            self.Copy()
            self.ReplaceSelection('')

    def Copy(self):
        """Copy selection and place it on the clipboard."""
        if self.CanCopy():
            ps1 = str(sys.ps1)
            ps2 = str(sys.ps2)
            command = self.GetSelectedText()
            command = command.replace(os.linesep + ps2, os.linesep)
            command = command.replace(os.linesep + ps1, os.linesep)
            command = self.lstripPrompt(text=command)
            data = wx.TextDataObject(command)
            self._clip(data)

    def CopyWithPrompts(self):
        """Copy selection, including prompts, and place it on the clipboard."""
        if self.CanCopy():
            command = self.GetSelectedText()
            data = wx.TextDataObject(command)
            self._clip(data)

    def CopyWithPromptsPrefixed(self):
        """Copy selection, including prompts prefixed with four
        spaces, and place it on the clipboard."""
        if self.CanCopy():
            command = self.GetSelectedText()
            spaces = ' ' * 4
            command = spaces + command.replace(os.linesep,
                                               os.linesep + spaces)
            data = wx.TextDataObject(command)
            self._clip(data)

    def _clip(self, data):
        if wx.TheClipboard.Open():
            wx.TheClipboard.UsePrimarySelection(False)
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Flush()
            wx.TheClipboard.Close()

    def Paste(self):
        """Replace selection with clipboard contents."""
        if self.CanPaste() and wx.TheClipboard.Open():
            ps2 = str(sys.ps2)
            if wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_TEXT)):
                data = wx.TextDataObject()
                if wx.TheClipboard.GetData(data):
                    self.ReplaceSelection('')
                    command = data.GetText()
                    command = command.rstrip()
                    command = self.fixLineEndings(command)
                    command = self.lstripPrompt(text=command)
                    command = command.replace(os.linesep + ps2, '\n')
                    command = command.replace(os.linesep, '\n')
                    command = command.replace('\n', os.linesep + ps2)
                    self.write(command)
            wx.TheClipboard.Close()

    def PasteAndRun(self):
        """Replace selection with clipboard contents, run commands."""
        if wx.TheClipboard.Open():
            ps1 = str(sys.ps1)
            ps2 = str(sys.ps2)
            if wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_TEXT)):
                data = wx.TextDataObject()
                if wx.TheClipboard.GetData(data):
                    endpos = self.GetTextLength()
                    self.SetCurrentPos(endpos)
                    startpos = self.promptPosEnd
                    self.SetSelection(startpos, endpos)
                    self.ReplaceSelection('')
                    text = data.GetText()
                    text = text.lstrip()
                    text = self.fixLineEndings(text)
                    text = self.lstripPrompt(text)
                    text = text.replace(os.linesep + ps1, '\n')
                    text = text.replace(os.linesep + ps2, '\n')
                    text = text.replace(os.linesep, '\n')
                    lines = text.split('\n')
                    commands = []
                    command = ''
                    for line in lines:
                        if line.strip() == ps2.strip():
                            # If we are pasting from something like a
                            # web page that drops the trailing space
                            # from the ps2 prompt of a blank line.
                            line = ''
                        if line.strip() != '' and line.lstrip() == line:
                            # New command.
                            if command:
                                # Add the previous command to the list.
                                commands.append(command)
                            # Start a new command, which may be multiline.
                            command = line
                        else:
                            # Multiline command. Add to the command.
                            command += '\n'
                            command += line
                    commands.append(command)
                    for command in commands:
                        command = command.replace('\n', os.linesep + ps2)
                        self.write(command)
                        self.processLine()
            wx.TheClipboard.Close()

    def wrap(self, wrap=True):
        """Sets whether text is word wrapped."""
        try:
            self.SetWrapMode(wrap)
        except AttributeError:
            return 'Wrapping is not available in this version.'

    def zoom(self, points=0):
        """Set the zoom level.

        This number of points is added to the size of all fonts.  It
        may be positive to magnify or negative to reduce."""
        self.SetZoom(points)
