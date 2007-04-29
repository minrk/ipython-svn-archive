# Standard library imports.
import compiler
import codeop
import re
import __builtin__

# Local imports.
from util import Bunch, make_quoted_expr


class Translator(object):
    """ A callable object that translates IPython commands into real Python
    code.
    """

    def __init__(self, config=None):

        # The configuration object.
        if config is None:
            config = Bunch(
                ESC_SHELL  = '!',
                ESC_HELP   = '?',
                ESC_MAGIC  = '%',
                ESC_QUOTE  = ',',
                ESC_QUOTE2 = ';',
                ESC_PAREN  = '/',
            )
        self.config = config

        # The mapping from escape characters to handler methods.
        self.esc_handlers = {
            self.config.ESC_PAREN  : self.handle_auto,
            self.config.ESC_QUOTE  : self.handle_auto,
            self.config.ESC_QUOTE2 : self.handle_auto,
            self.config.ESC_MAGIC  : self.handle_magic,
            self.config.ESC_HELP   : self.handle_help,
            self.config.ESC_SHELL  : self.handle_shell_escape,
        }

    def __call__(self, text):
        """ Actually translate.

        Parameters
        ----------
        text : str
            The raw (I)Python commands that the user entered.

        Returns
        -------

        """

        try:
            ast = compiler.parse(text)

            # If we get to this point, then the text is pure Python, so we can
            # pass it along. It does not need translation.
            return text
        except SyntaxError, e:
            # fixme: Try other translations!
            return text


    def handle_magic(self, line, pre, function, rest):
        """ Translate magic functions.
        """

        cmd = '%s__IP.ipmagic(%s)' % (pre, 
            make_quoted_expr(function + " " + rest))
        return cmd

    def handle_help(self, line, pre, function, rest):
        """ Try to get some help for the object.

        obj? or ?obj   -> basic information.
        obj?? or ??obj -> more details.
        """

        # We need to make sure that we don't process lines which would be
        # otherwise valid python, such as "x=1 # what?"
        try:
            codeop.compile_command(line)
        except SyntaxError:
            # We should only handle as help stuff which is NOT valid syntax
            if line[0]==self.ESC_HELP:
                line = line[1:]
            elif line[-1]==self.ESC_HELP:
                line = line[:-1]
            if line:
                # fixme: find the right function for this.
                self.magic_pinfo(line)
            else:
                # fixme: should give usage information here.
                pass

            # Empty string is needed here!
            return ''
        except:
            # Pass any other exceptions through to the normal handler.
            return line
        else:
            # If the code compiles ok, we should handle it normally
            return line

    def handle_shell_escape(self, line, pre, function, rest):
        """ Execute the line in a shell, empty return value.
        """

        # Example of a special handler. Others follow a similar pattern.
        if line.lstrip().startswith('!!'):
            # Rewrite function/rest to properly hold the call to %sx and
            # the actual command to be executed, so handle_magic can work
            # correctly.
            rest = '%s %s' % (function[2:], rest)
            function = 'sx'

            return self.handle_magic(
                '%ssx %s' % (self.ESC_MAGIC, line.lstrip()[2:]),
                pre, function, rest)
        else:
            cmd = line.lstrip().lstrip('!')
            line_out = '%s__IP.ipsystem(%s)' % (pre, make_quoted_expr(cmd))

            return line_out

    def handle_auto(self, line, pre, function, rest, obj):
        """
        """

        # fixme: implement auto-calling.
        return line

    def handle_alias(self, line, pre, function, rest):
        """
        """

        # fixme: implement aliases.
        return line


# fixme: The following class was an utterly incomplete attempt. Might want to
# simply start over, here.

#class IPythonTranslator(object):
#    """ An object that will do IPython translations on a single segment of code.
#    """
#
#    #### Configuration traits ####
#
#    # The code block.
#    text = Str
#
#    # The Translator object that spawned this one.
#    translator = Any
#
#    # The main namespace.
#    namespace = Dict
#
#    #### State traits ####
#
#    # A list of translated lines.
#    translated = List
#
#    #### Constants ####
#
#    # Regexp for splitting line contents into pre-char//first
#    # word-method//rest.  For clarity, each group in on one line.
#    #
#    # WARNING: update the regexp if the escapes are changed, as they
#    # are hardwired in.
#    #
#    # Don't get carried away with trying to make the autocalling catch too
#    # much:  it's better to be conservative rather than to trigger hidden
#    # evals() somewhere and end up causing side effects.
#    line_split = Constant(re.compile(r'^([\s*,;/])'
#                                     r'([\?\w\.]+\w*\s*)'
#                                     r'(\(?.*$)'))
#
#    def split_user_input(self, line):
#        """Split user input into pre-char (indentation), function part and rest.
#        """
#
#        lsplit = self.line_split.match(line)
#        if lsplit is None:
#            # no regexp match returns None
#            try:
#                function, rest = line.split(None, 1)
#            except ValueError:
#                function, rest = line,''
#            pre = re.match('^(\s*)(.*)', line).groups()[0]
#        else:
#            pre, function, rest = lsplit.groups()
#
#        return pre, function.strip(), rest
#
#
#    def _prefilter(self, line):
#        """ Calls different preprocessors, depending on the form of line.
#        """
#
#        stripped = line.strip()
#
#        if not stripped:
#            # Empty line
#            return ''
#
#        # For the rest, we need the structure of the input
#        pre, function, rest = self.split_user_input(line)
#
#        # fixme: try a user-defined prefilter here.
#
#        # First check for explicit escapes in the last/first character.
#        handler = None
#        if line.endswith(self.translator.ESC_HELP):
#            # ? can be at the end of the line.
#            handler = self.esc_handlers.get(line[-1], None)
#        if handler is None:
#            # Look at the first character of function, NOT of line, so we skip
#            # leading whitespace.
#            # Use [0:1] so we get '' when function is the empty string.
#            handler = self.esc_handlers.get(function[0:1])
#        if handler is not None:
#            return handler(line, pre, function, rest)
#
#        # Next check if we can automatically execute this thing.
#
#        # Let's try to find if the input line is a magic function.
#        info = None
#        if self.magic.has_magic(function):
#            # Now look in the various namespaces to make sure that this actually
#            # *is* a magic rather than a reference to an object.
#            info = self.magic.object_find(function)
#            if info['ismagic']:
#                # Be careful not to call magics when a variable assignment is
#                # being made (ls='hi', for example)
#                if (self.config.automagic and
#                    (len(rest) == 0 or rest[0] not in '!=()<>,')):
#                    return self.translator.handle_magic(line, pre, function, rest)
#                else:
#                    return line
#
#        # If the rest of the line begins with an (in)equality, assginment or
#        # function call, we should not call _ofind but simply execute it.
#        # This avoids spurious geattr() accesses on objects upon assignment.
#        #
#        # It also allows users to assign to either alias or magic names true
#        # python variables (the magic/alias systems always take second seat to
#        # true python code).
#        if rest and rest[0] in '!=()':
#            return line
#
#        if info is None:
#            # Let's try to ensure that self.magic.object_find is ONLY called
#            # when autocall is on.  Since it has inevitable potential side
#            # effects, at least having autocall off should be a guarantee to the
#            # user that no weird things will happen.
#            if self.config.autocall:
#                info = self.magic.object_find(function)
#            else:
#                # In this case, all that's left is either an alias or
#                # processing the line normally.
#                if function in self.alias_table:
#                    # If autocall is off, by not running object_find we won't
#                    # know whether the given name may also exist in one of the
#                    # user's namespace.  At this point, it's best to do a quick
#                    # check just to be sure that we don't let aliases shadow
#                    # variables.
#                    head = function.split('.', 1)[0]
#                    if (head in self.namespace or 
#                        head in self.internal_ns or
#                        head in __builtin__.__dict__):
#                        return line
#                    else:
#                        return self.translator.handle_alias(line, pre, function, rest)
#                 
#                else:
#                    return line
#        
#
#        if not info['found']:
#            return line
#        else:
#            if info['isalias']:
#                return self.translator.handle_alias(line, pre, function, rest)
#
#            if (self.config.autocall and
#                (# Only consider exclusion re if not "," or ";" autoquoting.
#                    (pre == self.config.ESC_QUOTE or 
#                     pre == self.config.ESC_QUOTE2 or 
#                     pre == self.config.ESC_PAREN) or 
#                     (not self.re_exclude_auto.match(rest))) and
#                self.re_fun_name.match(function) and 
#                callable(info['obj'])):
#
#                return self.translator.handle_auto(line, pre, function, rest, info['obj'])
#            else:
#                return line
#
#        # If we get here, we have a normal Python line.
#        return line











