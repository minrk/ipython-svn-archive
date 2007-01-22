#!/usr/bin/env python
"""IPython-enhanced doctest module with unittest integration.

This module is heavily based on the standard library's doctest module, but
enhances it with IPython support.  This enables docstrings to contain
unmodified IPython input and output pasted from real IPython sessions.

It should be possible to use this module as a drop-in replacement for doctest
whenever you wish to use IPython input.

Since the module absorbs all normal doctest functionality, you can use a mix of
both plain Python and IPython examples in any given module, though not in the
same docstring.

See a simple example at the bottom of this code which serves as self-test and
demonstration code.  Simply run this file (use -v for details) to run the
tests.

This module also contains routines to ease the integration of doctests with
regular unittest-based testing.  In particular, see the DocTestLoader class and
the makeTestSuite utility function.


Limitations:

 - IPython functions that produce output as a side-effect of calling a system
   process can NOT be doc-tested, since that output is not captured by doctest
   at runtime (things like 'ls', for example).

 - When generating examples for use as doctests, make sure that you have
   pretty-printing OFF.  This can be done either by starting ipython with the
   flag '--nopprint', by setting pprint to 0 in your ipythonrc file, or by
   interactively disabling it with %Pprint.  This is required so that IPython
   output matches that of normal Python, which is used by doctest for internal
   execution.

 - The underlying IPython used to run the code is started in 'classic' mode,
   which disables the output history.  So examples that rely on using
   previously numbered results (such as testing _35==True, for example) will
   fail.  The single-previous input '_' variable /is/ correctly set, so that
   can still be used (see example at the end of this file).

"""

# Standard library imports
import __builtin__
import doctest
import inspect
import re
import sys
import unittest

from doctest import *

###########################################################################
#
# We must start our own ipython object and heavily muck with it so that all the
# modifications IPython makes to system behavior don't send the doctest
# machinery into a fit.  This code should be considered a gross hack, but it
# gets the job done.

import IPython

# Disable terminal title setting, which confuses doctest.  This must be done
# BEFORE making the actual ipython instance
IPython.platutils.set_term_title = lambda x: None # make it a no-op

# Hack to restore __main__, which ipython modifies upon startup
_main = sys.modules.get('__main__')
ipython = IPython.Shell.IPShell(['--classic']).IP
sys.modules['__main__'] = _main

# Deactivate the various python system hooks added by ipython for
# interactive convenience so we don't confuse the doctest system
sys.displayhook = sys.__displayhook__
sys.excepthook = sys.__excepthook__

# So that ipython magics and aliases can be doctested
__builtin__._ip = IPython.ipapi.get()

###########################################################################

# A simple subclassing of the original with a different class name, so we can
# distinguish and treat differently IPython examples from pure python ones.
class IPExample(doctest.Example): pass

class IPDocTestParser(doctest.DocTestParser):
    """
    A class used to parse strings containing doctest examples.

    Note: This is a version modified to properly recognize IPython input and
    convert any IPython examples into valid Python ones.
    """
    # This regular expression is used to find doctest examples in a
    # string.  It defines three groups: `source` is the source code
    # (including leading indentation and prompts); `indent` is the
    # indentation of the first (PS1) line of the source code; and
    # `want` is the expected output (including leading indentation).

    # Classic Python prompts or default IPython ones
    _PS1_PY = r'>>>'
    _PS2_PY = r'\.\.\.'

    _PS1_IP = r'In\ \[\d+\]:'
    _PS2_IP = r'\ \ \ \.\.\.+:'

    _RE_TPL = r'''
        # Source consists of a PS1 line followed by zero or more PS2 lines.
        (?P<source>
            (?:^(?P<indent> [ ]*) (?P<ps1> %s) .*)    # PS1 line
            (?:\n           [ ]*  (?P<ps2> %s) .*)*)  # PS2 lines
        \n? # a newline
        # Want consists of any non-blank lines that do not start with PS1.
        (?P<want> (?:(?![ ]*$)    # Not a blank line
                     (?![ ]*%s)   # Not a line starting with PS1
                     (?![ ]*%s)   # Not a line starting with PS2
                     .*$\n?       # But any other line
                  )*)
                  '''

    _EXAMPLE_RE_PY = re.compile( _RE_TPL % (_PS1_PY,_PS2_PY,_PS1_PY,_PS2_PY),
                                 re.MULTILINE | re.VERBOSE)

    _EXAMPLE_RE_IP = re.compile( _RE_TPL % (_PS1_IP,_PS2_IP,_PS1_IP,_PS2_IP),
                                 re.MULTILINE | re.VERBOSE)

    def ip2py(self,source):
        """Convert input IPython source into valid Python."""
        out = []
        newline = out.append
        for line in source.splitlines():
            newline(ipython.prefilter(line,True))
        newline('')  # ensure a closing newline, needed by doctest
        return '\n'.join(out)

    def parse(self, string, name='<string>'):
        """
        Divide the given string into examples and intervening text,
        and return them as a list of alternating Examples and strings.
        Line numbers for the Examples are 0-based.  The optional
        argument `name` is a name identifying this string, and is only
        used for error messages.
        """
        string = string.expandtabs()
        # If all lines begin with the same indentation, then strip it.
        min_indent = self._min_indent(string)
        if min_indent > 0:
            string = '\n'.join([l[min_indent:] for l in string.split('\n')])

        output = []
        charno, lineno = 0, 0

        # Find all doctest examples in the string.  First, try them as Python
        # examples, then as IPython ones
        terms = list(self._EXAMPLE_RE_PY.finditer(string))
        if terms:
            # Normal Python example
            Example = doctest.Example
        else:
            # It's an ipython example
            terms = list(self._EXAMPLE_RE_IP.finditer(string))
            Example = IPExample
        
        for m in terms:
            # Add the pre-example text to `output`.
            output.append(string[charno:m.start()])
            # Update lineno (lines before this example)
            lineno += string.count('\n', charno, m.start())
            # Extract info from the regexp match.
            (source, options, want, exc_msg) = \
                     self._parse_example(m, name, lineno)
            # Create an Example, and add it to the list.
            if not self._IS_BLANK_OR_COMMENT(source):
                output.append(Example(source, want, exc_msg,
                                    lineno=lineno,
                                    indent=min_indent+len(m.group('indent')),
                                    options=options))
            # Update lineno (lines inside this example)
            lineno += string.count('\n', m.start(), m.end())
            # Update charno.
            charno = m.end()
        # Add any remaining post-example text to `output`.
        output.append(string[charno:])

        return output

    def _parse_example(self, m, name, lineno):
        """
        Given a regular expression match from `_EXAMPLE_RE` (`m`),
        return a pair `(source, want)`, where `source` is the matched
        example's source code (with prompts and indentation stripped);
        and `want` is the example's expected output (with indentation
        stripped).

        `name` is the string's name, and `lineno` is the line number
        where the example starts; both are used for error messages.
        """
        # Get the example's indentation level.
        indent = len(m.group('indent'))

        # Divide source into lines; check that they're properly
        # indented; and then strip their indentation & prompts.
        source_lines = m.group('source').split('\n')

        # We're using variable-length input prompts
        ps1 = m.group('ps1')
        ps2 = m.group('ps2')
        ps1_len = len(ps1)

        self._check_prompt_blank(source_lines, indent, name, lineno,ps1_len)
        if ps2:
            self._check_prefix(source_lines[1:], ' '*indent + ps2, name, lineno)

        source = '\n'.join([sl[indent+ps1_len+1:] for sl in source_lines])

        # Convert source input from IPython into valid Python syntax
        source = self.ip2py(source)

        # Divide want into lines; check that it's properly indented; and
        # then strip the indentation.  Spaces before the last newline should
        # be preserved, so plain rstrip() isn't good enough.
        want = m.group('want')
        want_lines = want.split('\n')
        if len(want_lines) > 1 and re.match(r' *$', want_lines[-1]):
            del want_lines[-1]  # forget final newline & spaces after it
        self._check_prefix(want_lines, ' '*indent, name,
                           lineno + len(source_lines))

        # Remove ipython output prompt that might be present in the first line
        want_lines[0] = re.sub(r'^Out\[\d+\]: \s*?\n?','',want_lines[0])

        want = '\n'.join([wl[indent:] for wl in want_lines])

        # If `want` contains a traceback message, then extract it.
        m = self._EXCEPTION_RE.match(want)
        if m:
            exc_msg = m.group('msg')
        else:
            exc_msg = None

        # Extract options from the source.
        options = self._find_options(source, name, lineno)

        return source, options, want, exc_msg

    def _check_prompt_blank(self, lines, indent, name, lineno, ps1_len):
        """
        Given the lines of a source string (including prompts and
        leading indentation), check to make sure that every prompt is
        followed by a space character.  If any line is not followed by
        a space character, then raise ValueError.

        Note: IPython-modified version which takes the input prompt length as a
        parameter, so that prompts of variable length can be dealt with.
        """
        space_idx = indent+ps1_len
        min_len = space_idx+1
        for i, line in enumerate(lines):
            if len(line) >=  min_len and line[space_idx] != ' ':
                raise ValueError('line %r of the docstring for %s '
                                 'lacks blank after %s: %r' %
                                 (lineno+i+1, name,
                                  line[indent:space_idx], line))


class IPDocTestLoader(unittest.TestLoader):
    """A test loader with IPython-enhanced doctest support.

    Instances of this loader will automatically add doctests found in a module
    to the test suite returned by the loadTestsFromModule method.  In
    addition, at initialization time a string of doctests can be given to the
    loader, enabling it to add doctests to a module which didn't have them in
    its docstring, coming from an external source."""

    
    def __init__(self,doctests=None,dt_module=None,test_finder=None):
        """Initialize the test loader.

        Optional inputs:
          - doctests(None): a string containing the text to be assigned as the
          __doc__ attribute for a module in the loadTestsFromModule method.

          - dt_module(None): a module object whose docstrings should be
          scanned for embedded doctests, following the normal doctest API.
        """
        
        self.doctests = doctests
        self.dt_module = dt_module
        if test_finder is None:
            test_finder = doctest.DocTestFinder(parser=IPDocTestParser())
        self.test_finder = test_finder

    def loadTestsFromModule(self, module):
        """Return a suite of all tests cases contained in the given module.

        If the loader was initialized with a doctests argument, then this
        string is assigned as the module's docstring."""

        suite = super(self.__class__,self).loadTestsFromModule(module)
        if self.doctests is not None:
            module.__doc__ = self.doctests
        try:
            suite.addTest(doctest.DocTestSuite(module,
                                               test_finder=self.test_finder))
        except ValueError:
            pass
        # Add docstring tests from module, if given at construction time
        if self.dt_module is not None:
            suite.addTest(doctest.DocTestSuite(self.dt_module,
                                               test_finder=self.test_finder))
        return suite

def my_import(name):
    """Module importer - taken from the python documentation.

    This function allows importing names with dots in them."""
    
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

def makeTestSuite(module_name,module=None):
    """Make a TestSuite object for a given module, specified by name.

    This extracts all the doctests associated with a module using an
    IPDocTestLoader object.

    Inputs:

      - module_name: a string containing 
    Optional inputs:
    """

    mod = my_import(module_name)
    return IPDocTestLoader(dt_module=module).loadTestsFromModule(mod)

def testmod(m=None,name=None):
    
    # If no module was given, then use __main__.
    if m is None:
        # DWA - m will still be None if this wasn't invoked from the command
        # line, in which case the following TypeError is about as good an error
        # as we should expect
        m = sys.modules.get('__main__')

    # Check that we were actually given a module.
    if not inspect.ismodule(m):
        raise TypeError("testmod: module required; %r" % (m,))

    # If no name was given, then use the module's name.
    if name is None:
        name = m.__name__

    # Find, parse, and run all tests in the given module.
    finder = DocTestFinder(parser=IPDocTestParser())

    runner = DocTestRunner()

    for test in finder.find(m, name):
        runner.run(test)

    runner.summarize()

    return runner.failures, runner.tries

# Simple testing and example code
if __name__ == "__main__":
    
    def ipfunc():
        """
        Some ipython tests...

        In [1]: import os

        In [2]: cd /
        /

        In [3]: 2+3
        Out[3]: 5

        In [26]: for i in range(3):
           ....:     print i,
           ....:     print i+1,
           ....:
        0 1 1 2 2 3


        Examples that access the operating system work:
        
        In [19]: cd /tmp
        /tmp

        In [20]: mkdir foo_ipython

        In [21]: cd foo_ipython
        /tmp/foo_ipython

        In [23]: !touch bar baz

        # We unfortunately can't just call 'ls' because its output is not
        # seen by doctest, since it happens in a separate process
        
        In [24]: os.listdir('.')
        Out[24]: ['bar', 'baz']

        In [25]: cd /tmp
        /tmp

        In [26]: rm -rf foo_ipython


        It's OK to use '_' for the last result, but do NOT try to use IPython's
        numbered history of _NN outputs, since those won't exist under the
        doctest environment:
        
        In [7]: 3+4
        Out[7]: 7

        In [8]: _+3
        Out[8]: 10
  
        """

    def pyfunc():
        """
        Some pure python tests...

        >>> import os

        >>> 2+3
        5

        >>> for i in range(3):
        ...     print i,
        ...     print i+1,
        ...
        0 1 1 2 2 3
        """

    # Call the global testmod() just like you would with normal doctest
    testmod()
