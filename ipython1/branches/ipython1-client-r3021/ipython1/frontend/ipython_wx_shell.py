#!/usr/bin/env python
"""
Widget for a front-end to ipython, using wxStyledTextCtrl.

This file was originally inspired from PyShell, written by Pratick K. O'Brien
<pobrien@orbtech.com>.
"""

__author__ = """Eric Jones <eric@enthought.com>, 
                 Gael Varoquaux <gael.varoquaux@normalesup.org>"""
__version__ = "0.0.1"

# standard imports
import keyword
import os
import sys
import time

# wx imports
import wx
from wx import stc

# PyCrust imports
from wx.py.buffer import Buffer
from wx.py import dispatcher
from wx.py import editwindow

# ipython imports
from ipython1.core.interpreter import Interpreter as IPythonInterpreter

from ipreadline import IPReadline

NAVKEYS = (wx.WXK_END, wx.WXK_LEFT, wx.WXK_RIGHT,
           wx.WXK_UP, wx.WXK_DOWN, wx.WXK_PRIOR, wx.WXK_NEXT)


sys.ps3 = '<-- '  # Input prompt.

class Shell(editwindow.EditWindow):
    """WxPython frontend for ipython."""

    def __init__(self, parent, id=-1, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.CLIP_CHILDREN,
                 introText='', locals=None, InterpClass=None,
                 *args, **kwds):
        """ Create Shell instance.
        """
        editwindow.EditWindow.__init__(self, parent, id, pos, size, style)

        # Set the shell to automatically wrap lines instead of scrolling when
        # lines are wider than the shell width.
        self.wrap()

        # We want all the variables available in __main__ within our local
        # dict. (
        # fixme: Do we really want this?  Is this something handled by
        #        IPython?
        if locals is None:
            import __main__
            locals = __main__.__dict__

        self._ipython_interpreter = IPythonInterpreter(user_ns=locals)

        self.ip_readline = IPReadline(interpreter=self._ipython_interpreter)

        # Set up the buffer.
        # FIXME: What is this?
        self.buffer = Buffer()

        # Find out for which keycodes the interpreter will autocomplete.
        self.autoCompleteKeys = [] #self.interp.getAutoCompleteKeys()

        # Keep track of the last non-continuation prompt positions.
        self.promptPosStart = 0
        self.promptPosEnd = 0

        # Keep track of multi-line commands.
        self.more = False

        #seb add mode for "free edit"
        self.noteMode = 0
        self.MarkerDefine(0,stc.STC_MARK_ROUNDRECT)  # marker for hidden
        self.searchTxt = ""

        # Assign handlers for keyboard events.
        self.Bind(wx.EVT_CHAR, self.OnChar)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

        # Assign handler for idle time.
        self.waiting = False
        self.Bind(wx.EVT_IDLE, self.OnIdle)

        # Display the introductory banner information.
        self.showIntro(introText)

        # Assign some pseudo keywords to the interpreter's namespace.
        self.setBuiltinKeywords()

        self.prompt()

        wx.CallAfter(self.ScrollToLine, 0)

    def OnIdle(self, event):
        """Free the CPU to do other things."""
        if self.waiting:
            time.sleep(0.05)
        event.Skip()

    def showIntro(self, text=''):
        """Display introductory text in the shell."""
        # fixme: We need to get this from IPython
        text = "Gael's a winnie and Fernando is too.\n" \
               "Oh yeah, and this is a Python interpreter punk."
        if text:
            self.write(text)

    def setBuiltinKeywords(self):
        """Create pseudo keywords as part of builtins.

        This sets "close", "exit" and "quit" to a helpful string.
        """
        import __builtin__
        __builtin__.close = __builtin__.exit = __builtin__.quit = \
            'Click on the close button to leave the application.'

    def quit(self):
        """Quit the application."""
        # XXX Good enough for now but later we want to send a close event.
        # In the close event handler we can make sure they want to
        # quit.  Other applications, like PythonCard, may choose to
        # hide rather than quit so we should just post the event and
        # let the surrounding app decide what it wants to do.
        self.write('Click on the close button to leave the application.')

    def execStartupScript(self, startupScript):
        """Execute the user's PYTHONSTARTUP script if they have one."""
        if startupScript and os.path.isfile(startupScript):
            text = 'Startup script executed: ' + startupScript
            self.ip_readline.push_text('print %r; execfile(%r)' % 
                                                (text, startupScript))
            #self.interp.startupScript = startupScript
        else:
            self.ip_readline.push_text('')

    def OnChar(self, event):
        """Keypress event handler.

        Only receives an event if OnKeyDown calls event.Skip() for the
        corresponding event."""

        if self.noteMode:
            event.Skip()
            return

        # Prevent modification of previously submitted
        # commands/responses.
        if not self.CanEdit():
            return
        key = event.GetKeyCode()
        currpos = self.GetCurrentPos()
        stoppos = self.promptPosEnd
        # Return (Enter) needs to be ignored in this handler.
        if key in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
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
            self.autoCallTipShow(command, self.GetCurrentPos() == self.GetTextLength())
        else:
            # Allow the normal event handling to take place.
            event.Skip()



    def OnKeyDown(self, event):
        """Key down event handler."""

        key = event.GetKeyCode()
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

        if controlDown and shiftDown and key in (ord('F'), ord('f')):
            li = self.GetCurrentLine()
            m = self.MarkerGet(li)
            if m & 1<<0:
                startP = self.PositionFromLine(li)
                self.MarkerDelete(li, 0)
                maxli = self.GetLineCount()
                li += 1 # li stayed visible as header-line
                li0 = li
                while li<maxli and self.GetLineVisible(li) == 0:
                    li += 1
                endP = self.GetLineEndPosition(li-1)
                self.ShowLines(li0, li-1)
                self.SetSelection( startP, endP ) # select reappearing text to allow "hide again"
                return
            startP,endP = self.GetSelection()
            endP-=1
            startL,endL = self.LineFromPosition(startP), self.LineFromPosition(endP)

            if endL == self.LineFromPosition(self.promptPosEnd): # never hide last prompt
                endL -= 1

            m = self.MarkerGet(startL)
            self.MarkerAdd(startL, 0)
            self.HideLines(startL+1,endL)
            self.SetCurrentPos( startP ) # to ensure caret stays visible !

        if key == wx.WXK_F12: #seb
            if self.noteMode:
                # self.promptPosStart not used anyway - or ?
                self.promptPosEnd = self.PositionFromLine( self.GetLineCount()-1 ) + len(str(sys.ps1))
                self.GotoLine(self.GetLineCount())
                self.GotoPos(self.promptPosEnd)
                self.prompt()  #make sure we have a prompt
                self.SetCaretForeground("black")
                self.SetCaretWidth(1)    #default
                self.SetCaretPeriod(500) #default
            else:
                self.SetCaretForeground("red")
                self.SetCaretWidth(4)
                self.SetCaretPeriod(0) #steady

            self.noteMode = not self.noteMode
            return
        if self.noteMode:
            event.Skip()
            return

        # Return (Enter) is used to submit a command to the
        # interpreter.
        if (not controlDown and not shiftDown and not altDown) and key in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            if self.CallTipActive():
                self.CallTipCancel()
            self.processLine()

        # Complete Text (from already typed words)
        elif shiftDown and key in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            self.OnShowCompHistory()

        # Ctrl+Return (Ctrl+Enter) is used to insert a line break.
        elif controlDown and key in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            if self.CallTipActive():
                self.CallTipCancel()
            if currpos == endpos:
                self.processLine()
            else:
                self.insertLineBreak()

        # Let Ctrl-Alt-* get handled normally.
        elif controlDown and altDown:
            event.Skip()

        # Clear the current, unexecuted command.
        elif key == wx.WXK_ESCAPE:
            if self.CallTipActive():
                event.Skip()
            else:
                self.clearCommand()

        # Clear the current command
        elif key == wx.WXK_BACK and controlDown and shiftDown:
            self.clearCommand()

        # Increase font size.
        elif controlDown and key in (ord(']'), wx.WXK_NUMPAD_ADD):
            dispatcher.send(signal='FontIncrease')

        # Decrease font size.
        elif controlDown and key in (ord('['), wx.WXK_NUMPAD_SUBTRACT):
            dispatcher.send(signal='FontDecrease')

        # Default font size.
        elif controlDown and key in (ord('='), wx.WXK_NUMPAD_DIVIDE):
            dispatcher.send(signal='FontDefault')

        # Cut to the clipboard.
        elif (controlDown and key in (ord('X'), ord('x'))) \
                 or (shiftDown and key == wx.WXK_DELETE):
            self.Cut()

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
        elif key == wx.WXK_HOME:
            home = self.promptPosEnd
            if currpos > home:
                self.SetCurrentPos(home)
                if not selecting and not shiftDown:
                    self.SetAnchor(home)
                    self.EnsureCaretVisible()
            else:
                event.Skip()

        #
        # The following handlers modify text, so we need to see if
        # there is a selection that includes text prior to the prompt.
        #
        # Don't modify a selection with text prior to the prompt.
        elif selecting and key not in NAVKEYS and not self.CanEdit():
            pass

        # Paste from the clipboard.
        elif (controlDown and not shiftDown and key in (ord('V'), ord('v'))) \
                 or (shiftDown and not controlDown and key == wx.WXK_INSERT):
            self.Paste()

        # manually invoke AutoComplete and Calltips
        elif controlDown and key == wx.WXK_SPACE:
            self.OnCallTipAutoCompleteManually(shiftDown)

        # Paste from the clipboard, run commands.
        elif controlDown and shiftDown and key in (ord('V'), ord('v')):
            self.PasteAndRun()

        # Replace with the previous command from the history buffer.
        elif (controlDown and key == wx.WXK_UP) \
                 or (altDown and key in (ord('P'), ord('p'))):
            self.replaceFromHistory(step=-1)

        # Replace with the next command from the history buffer.
        elif (controlDown and key == wx.WXK_DOWN) \
                 or (altDown and key in (ord('N'), ord('n'))):
            self.replaceFromHistory(step=+1)

        # Insert the previous command from the history buffer.
        elif (shiftDown and key == wx.WXK_UP) and self.CanEdit():
            self.OnHistoryInsert(step=+1)

        # Insert the next command from the history buffer.
        elif (shiftDown and key == wx.WXK_DOWN) and self.CanEdit():
            self.OnHistoryInsert(step=-1)

        # Search up the history for the text in front of the cursor.
        elif key == wx.WXK_F8:
            self.OnHistorySearch()

        # Don't backspace over the latest non-continuation prompt.
        elif key == wx.WXK_BACK:
            if selecting and self.CanEdit():
                event.Skip()
            elif currpos > self.promptPosEnd:
                event.Skip()

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


    def OnShowCompHistory(self):
        """Show possible autocompletion Words from already typed words."""
        # FIXME: To be done
        pass

##        #copy from history
##        his = self.history[:]
##
##        #put together in one string
##        joined = " ".join (his)
##        import re
##
##        #sort out only "good" words
##        newlist = re.split("[ \.\[\]=}(\)\,0-9\"]", joined)
##
##        #length > 1 (mix out "trash")
##        thlist = []
##        for i in newlist:
##            if len (i) > 1:
##                thlist.append (i)
##
##        #unique (no duplicate words)
##        unlist = [thlist[i] 
##                    for i in xrange(len(thlist)) 
##                    if thlist[i] not in thlist[:i]]
##
##        #sort lowercase
##        unlist.sort(lambda a, b: cmp(a.lower(), b.lower()))
##
##        #this is more convenient, isn't it?
##        self.AutoCompSetIgnoreCase(True)
##
##        #join again together in a string
##        stringlist = " ".join(unlist)
##
##        #how big is the offset?
##        cpos = self.GetCurrentPos() - 1
##        while chr (self.GetCharAt (cpos)).isalnum():
##            cpos -= 1
##
##        #the most important part
##        self.AutoCompShow(self.GetCurrentPos() - cpos -1, stringlist)
##

    def clearCommand(self):
        """Delete the current, unexecuted command."""
        startpos = self.promptPosEnd
        endpos = self.GetTextLength()
        self.SetSelection(startpos, endpos)
        self.ReplaceSelection('')
        self.more = False

    def replaceFromHistory(self, step):
        """Replace selection with command from the history buffer."""
        current_command = self.get_current_command()
        # FIXME: This works only for step in (1, -1)
        if step == -1:
            command = self.ip_readline.get_history_item_previous(
                                                            current_command)
        elif step == 1:
            command = self.ip_readline.get_history_item_next(
                                                            current_command)
        else:
            return
        if command is not None:
            self.clearCommand()
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
        ### XXX: To be implemented
        pass

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

    def get_current_command(self):
        thepos = self.GetCurrentPos()
        startpos = self.promptPosEnd
        endpos = self.GetTextLength()
        # Fixme: the ps2 prompt must be requested from the engine
        ps2 = str(sys.ps2)
        if self.CanEdit():
            self.SetCurrentPos(endpos)
            # fixme: commented out for now.
            #self.interp.more = False
            command = self.GetTextRange(startpos, endpos)
            lines = command.split(os.linesep + ps2)
            # Don't strip of whitespace, so we know when to stop reading input
            # (the user types in blank input lines)
            command = '\n'.join(lines)

            # fixme: commented out to get rid of reader...
            #if self.reader.isreading:
            #    if not command:
            #        # Match the behavior of the standard Python shell
            #        # when the user hits return without entering a
            #        # value.
            #        command = '\n'
            #    self.reader.input = command
            #    self.write(os.linesep)
            #else:
            #    self.push(command)
            #    wx.FutureCall(1, self.EnsureCaretVisible)
            return command

    def processLine(self):
        """Process the line of text at which the user hit Enter."""

        # The user hit ENTER and we need to decide what to do. They
        # could be sitting on any line in the shell.
        command = self.get_current_command()
        if command is not None:
            self.push(command)
            wx.FutureCall(1, self.EnsureCaretVisible)

        # Or replace the current command with the other command.
        else:
            # If the line contains a command (even an invalid one).
            if self.getCommand(rstrip=False):
                command = self.getMultilineCommand()
                self.clearCommand()
                self.write(command)
            # Otherwise, put the cursor back where we started.
            else:
                self.SetCurrentPos(thepos)
                self.SetAnchor(thepos)

    def getMultilineCommand(self, rstrip=True):
        """Extract a multi-line command from the editor.

        The command may not necessarily be valid Python syntax."""
        # XXX Need to extract real prompts here. Need to keep track of
        # the prompt every time a command is issued.
        # fixme: these will come from the ipython engine.
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

    def handle_output(self, output):

        # First check for the errors.
        if not hasattr(output, 'result_dict'):
            # No code has been executed.
            self.write(output)
            return
        elif 'traceback' in output.result_dict:
            print 'found error'
            output_text = output.result_dict['traceback']['plain']

        # Now check if any output was generated.
        else:
            output_text = str(output)

        self.write(output_text)

    def push(self, command, silent = False):
        """Send command to the interpreter for execution."""
        if not silent:
            self.write(os.linesep)
        busy = wx.BusyCursor()
        self.waiting = True

        # Execute the code.
        # fixme: Need to handle the case when a line doesn't represent a full
        #        line of code (like the more part of the old interpreter)
        ip_output, self.more = self.ip_readline.push_text(command)

        if isinstance(ip_output,dict):
            self.write(''.join(ip_output['exception_value']))
            self.waiting = False
            return

        if not hasattr(ip_output, 'result_dict'):
            # No command was executed
            self.waiting = False
            return

        print ip_output.result_dict  # dbg

        # If there was any output from the ipython, write out an output prompt
        # and the output results pretty printed to the window.
        self.handle_output(ip_output)

        self.waiting = False
        del busy

        if not silent:
            self.prompt(ip_output.prompt_num)

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

    def prompt(self, number=None):
        """Display proper prompt for the context: ps1, ps2 or ps3.

        If this is a continuation line, autoindent as necessary."""
        # fixme: commented out to get rid of reader. delete if it works.
        #isreading = self.reader.isreading
        skip = False
        # fixme: commented out to get rid of reader. delete if it works.
        #if isreading:
        if 0:
            prompt = str(sys.ps3)
        elif self.more:
            1/0
            prompt = str(sys.ps2)
        else:
            # We've stuck in the IPython prompt here using the number returned
            # from execution if it existed.
            if number is None:
                number = "1"

            prompt = "In [%s]: " % number
            prompt = prompt

        pos = self.GetCurLine()[1]
        if pos > 0:
            #if isreading:
            if 0:
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

    def clear(self):
        """Delete all text from the shell."""
        self.ClearAll()

    def autoCompleteShow(self, command, offset = 0):
        """Display auto-completion popup list."""
        self.AutoCompSetAutoHide(self.autoCompleteAutoHide)
        self.AutoCompSetIgnoreCase(self.autoCompleteCaseInsensitive)
        # fixme: commented out to get rid of interp.
        #list = self.interp.getAutoCompleteList(command,
        #            includeMagic=self.autoCompleteIncludeMagic,
        #            includeSingle=self.autoCompleteIncludeSingle,
        #            includeDouble=self.autoCompleteIncludeDouble)
        list = []
        if list:
            options = ' '.join(list)
            #offset = 0
            self.AutoCompShow(offset, options)

    def autoCallTipShow(self, command, insertcalltip = True, forceCallTip = False):
        """Display argument spec and docstring in a popup window."""
        if self.CallTipActive():
            self.CallTipCancel()
        # fixme: put call to ipython in.
#        (name, argspec, tip) = `.getCallTip(command)
#        if tip:
#            dispatcher.send(signal='Shell.calltip', sender=self, calltip=tip)
#        if not self.autoCallTip and not forceCallTip:
#            return
#        if argspec and insertcalltip and self.callTipInsert:
#            startpos = self.GetCurrentPos()
#            self.write(argspec + ')')
#            endpos = self.GetCurrentPos()
#            self.SetSelection(endpos, startpos)
#        if tip:
#            curpos = self.GetCurrentPos()
#            tippos = curpos - (len(name) + 1)
#            fallback = curpos - self.GetColumn(curpos)
#            # In case there isn't enough room, only go back to the
#            # fallback.
#            tippos = max(tippos, fallback)
#            self.CallTipShow(tippos, tip)

    def OnCallTipAutoCompleteManually (self, shiftDown):
        """AutoComplete and Calltips manually."""
        if self.AutoCompActive():
            self.AutoCompCancel()
        currpos = self.GetCurrentPos()
        stoppos = self.promptPosEnd

        cpos = currpos
        #go back until '.' is found
        pointavailpos = -1
        while cpos >= stoppos:
            if self.GetCharAt(cpos) == ord ('.'):
                pointavailpos = cpos
                break
            cpos -= 1

        #word from non whitespace until '.'
        if pointavailpos != -1:
            #look backward for first whitespace char
            textbehind = self.GetTextRange (pointavailpos + 1, currpos)
            pointavailpos += 1

            if not shiftDown:
                #call AutoComplete
                stoppos = self.promptPosEnd
                textbefore = self.GetTextRange(stoppos, pointavailpos)
                self.autoCompleteShow(textbefore, len (textbehind))
            else:
                #call CallTips
                cpos = pointavailpos
                begpos = -1
                while cpos > stoppos:
                    if chr(self.GetCharAt(cpos)).isspace():
                        begpos = cpos
                        break
                    cpos -= 1
                if begpos == -1:
                    begpos = cpos
                ctips = self.GetTextRange (begpos, currpos)
                ctindex = ctips.find ('(')
                if ctindex != -1 and not self.CallTipActive():
                    #insert calltip, if current pos is '(', otherwise show it only
                    self.autoCallTipShow(ctips[:ctindex + 1],
                        self.GetCharAt(currpos - 1) == ord('(') and self.GetCurrentPos() == self.GetTextLength(),
                        True)


    def writeOut(self, text):
        """Replacement for stdout."""
        self.write(text)

    def writeErr(self, text):
        """Replacement for stderr."""
        self.write(text)

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
        if self.GetSelectionStart() != self.GetSelectionEnd():
            if self.GetSelectionStart() >= self.promptPosEnd \
                   and self.GetSelectionEnd() >= self.promptPosEnd:
                return True
            else:
                return False
        else:
            return self.GetCurrentPos() >= self.promptPosEnd

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
        text = ''
        if wx.TheClipboard.Open():
            if wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_TEXT)):
                data = wx.TextDataObject()
                if wx.TheClipboard.GetData(data):
                    text = data.GetText()
            wx.TheClipboard.Close()
        if text:
            self.Execute(text)


    def Execute(self, text):
        """Replace selection with text and run commands."""
        ps1 = str(sys.ps1)
        ps2 = str(sys.ps2)
        endpos = self.GetTextLength()
        self.SetCurrentPos(endpos)
        startpos = self.promptPosEnd
        self.SetSelection(startpos, endpos)
        self.ReplaceSelection('')
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
            lstrip = line.lstrip()
            if line.strip() != '' and lstrip == line and \
                    lstrip[:4] not in ['else','elif'] and \
                    lstrip[:6] != 'except':
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


    def LoadSettings(self, config):
        self.autoComplete              = config.ReadBool('Options/AutoComplete', True)
        self.autoCompleteIncludeMagic  = config.ReadBool('Options/AutoCompleteIncludeMagic', True)
        self.autoCompleteIncludeSingle = config.ReadBool('Options/AutoCompleteIncludeSingle', True)
        self.autoCompleteIncludeDouble = config.ReadBool('Options/AutoCompleteIncludeDouble', True)

        self.autoCallTip = config.ReadBool('Options/AutoCallTip', True)
        self.callTipInsert = config.ReadBool('Options/CallTipInsert', True)
        self.SetWrapMode(config.ReadBool('View/WrapMode', True))

        useAA = config.ReadBool('Options/UseAntiAliasing', self.GetUseAntiAliasing())
        self.SetUseAntiAliasing(useAA)
        self.lineNumbers = config.ReadBool('View/ShowLineNumbers', True)
        self.setDisplayLineNumbers (self.lineNumbers)
        zoom = config.ReadInt('View/Zoom/Shell', -99)
        if zoom != -99:
            self.SetZoom(zoom)


    def SaveSettings(self, config):
        config.WriteBool('Options/AutoComplete', self.autoComplete)
        config.WriteBool('Options/AutoCompleteIncludeMagic', self.autoCompleteIncludeMagic)
        config.WriteBool('Options/AutoCompleteIncludeSingle', self.autoCompleteIncludeSingle)
        config.WriteBool('Options/AutoCompleteIncludeDouble', self.autoCompleteIncludeDouble)
        config.WriteBool('Options/AutoCallTip', self.autoCallTip)
        config.WriteBool('Options/CallTipInsert', self.callTipInsert)
        config.WriteBool('Options/UseAntiAliasing', self.GetUseAntiAliasing())
        config.WriteBool('View/WrapMode', self.GetWrapMode())
        config.WriteBool('View/ShowLineNumbers', self.lineNumbers)
        config.WriteInt('View/Zoom/Shell', self.GetZoom())

if __name__ == '__main__':
    class MainWindow(wx.Frame):
        def __init__(self, parent, id, title):
            wx.Frame.__init__(self, parent, id, title, size=(300,250))
            self._sizer = wx.BoxSizer(wx.VERTICAL)
            self.shell = Shell(self)
            self._sizer.Add(self.shell, 1, wx.EXPAND)
            self.SetSizer(self._sizer)
            self.SetAutoLayout(1)
            self.Show(True)

    app = wx.PySimpleApp()
    frame = MainWindow(None, wx.ID_ANY, 'Ipython')
    frame.SetSize((780, 460))
    shell = frame.shell

    app.MainLoop()

