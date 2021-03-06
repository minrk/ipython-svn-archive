"""
IPReadline: interface between the Interpreter and the FrontEnd. 
"""

from ipython1.core.interpreter import Interpreter, COMPILER_ERROR, \
                COMPLETE_INPUT, INCOMPLETE_INPUT

from ipython1.core.history import FrontEndHistory

# XXX - Get this info from the interpreter, not from readline (since we may
# well NOT have readline around)
from readline import get_completer_delims

completer_delims = get_completer_delims()


class PendingResult(object):
    """ This should probably be used in the long term, when running in
    multi-threaded mode (one event-loop, one execution thread).
    """
    pass


class InterpreterResult(object):
    """ Result of the execution of code on the interpreter. This object
        contain all the information returned by the interpreter, and adds
        a method to display, that can be used or not by the frontend.
    """

    def __init__(self, result_dict):
        self.prompt_num = result_dict['number']
        self.result_dict = result_dict

    def __str__(self):
        result_dict = self.result_dict
        out_string = ""
        if 'stdout' in result_dict:
            out_string += result_dict['stdout']
        if 'display' in result_dict:
            result_dict['pprint'] = result_dict['display']['pprint']
            out_string += "Out[%(number)i]: %(pprint)s" % result_dict
        return out_string


class IPReadline(object):
    """
    IPReadline: interface between the Interpreter and the FrontEnd.

    The main job of this class is to decide what events to trigger on the
    interpreter, given user interaction (ie keypress). It sits between
    the Interpreter, wich may be on a distant machine, and to wich calls
    can be expensive, and the FrontEnd, in which we want to put as little
    logic as possible. 
    
    The FrontEnd, manages its line-buffer (moves the cursors, add the
    characters) but asks the IPReadline what to do with an user input
    throught the "process_key" method (to be implemented).

    XXX: Currently the interpreter is local and sits in the same process.
    However we need to be able to have a process boundary between the
    interpreter and the readline. This will probably be implemented by
    an adapter interpreter.
    """
    
    
    # History cursor: the position of the history refered from the start
    # of the history list.
    history_index = 0

    def __init__(self, interpreter=None, history=None):
        if interpreter is None:
            self.interpreter = Interpreter()
        else:
            self.interpreter = interpreter
        if history is None:
            self.history = FrontEndHistory(
                        input_cache=self.interpreter.get_history_input_cache()
                        + [''])
        else:
            self.history = history

    def process_key(self, char, buffer, position, insert=True):
        """ called when a char is entered in the current buffer (ie line)
        at the given position. The return argument is what will actually
        be added to the buffer, in insert or override mode.
        
        This is where the translation of keypresses in events (history,
        tab-completion...) gets implemented.
        """
        # FIXME: this should process key events rather than simple chars,
        # the difficulty is implementing the toolkit abstraction
        if char == "\n":
            return self.push_text(buffer[:position] + char +
                                                            buffer[position])
        if char == "(":
            self.fetch_docstring()
        return None

    def push_text(self, text):
        """ Ask the engine if the buffer is complete. If so, sends the 
            given text to the engine.

            The return values are

            X, more

            X can be several things (FIXME!), more is a boolean indicating
            whether more input is expected. """
        
        is_complete = self.interpreter.feed_block(text)
        print "Is complete ?", is_complete  # dbg
        if is_complete[0] == INCOMPLETE_INPUT:
            return "\n",True
        elif is_complete[0] == COMPILER_ERROR:
            # FIXME: Hack, there should really be user feedback for an
            # error.
            #print 'ERROR:',self.interpreter.message  # dbg
            return self.interpreter.message,False
        elif is_complete[0] == COMPLETE_INPUT:
            result_dict = self.interpreter.execute(text)
            # FIXME: This is blocking. It should be easy to switch from a
            # non-block (threaded) behavior) to a blocking behavior.
            # return PendingResult()

            ### Sync the local history with the interpreter's ###
            # First remove the current edited line:
            self.history.input_cache.pop()
            self.interpreter.get_history_input_after(
                        len(self.history.input_cache))
            self.history.input_cache.extend(
                    self.interpreter.get_history_input_after(
                        len(self.history.input_cache)))
            self.history_index = len(self.history.input_cache) 
            # Add a blank line at the end of the history.
            self.history.input_cache.append('')
            return InterpreterResult(result_dict), False

    def fetch_docstring(self, position):
        pass
        ## return self.interpreter.document(self.line, word) 

    def get_current_word(self, position):
        word = self.line[:position]
        for delim in completer_delims:
            word = word.split(delim)[-1]
        return word

    def get_history_item_previous(self, current_line):
        """ Returns previous history string and decrement history cursor.
        """
        new_cursor = self.history_index - 1
        command = self.history.get_history_item(new_cursor)
        if command is not None:
            self.history.input_cache[self.history_index] = current_line
            self.history_index = new_cursor
        return command

    def get_history_item_next(self, current_line):
        """ Returns next history string and increment history cursor.
        """
        new_cursor = self.history_index + 1
        command = self.history.get_history_item(new_cursor)
        if command is not None:
            self.history.input_cache[self.history_index] = current_line
            self.history_index = new_cursor
        return command

    def complete(self, position):
        word = self.get_docstring(position)
        completion = self.interpreter.complete(self.line, position)
        return completion

