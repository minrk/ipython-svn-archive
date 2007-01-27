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

# Hack to restore __main__, which ipython modifies upon startup
_main = sys.modules.get('__main__')
ipython = IPython.Shell.IPShell(['--classic','--noterm_title']).IP
sys.modules['__main__'] = _main

# Deactivate the various python system hooks added by ipython for
# interactive convenience so we don't confuse the doctest system
sys.displayhook = sys.__displayhook__
sys.excepthook = sys.__excepthook__

# So that ipython magics and aliases can be doctested
__builtin__._ip = IPython.ipapi.get()


# runner
from IPython.irunner import IPythonRunner
iprunner = IPythonRunner(echo=False)

###########################################################################

# A simple subclassing of the original with a different class name, so we can
# distinguish and treat differently IPython examples from pure python ones.
class IPExample(doctest.Example): pass

class IPExternalExample(doctest.Example):
    """Doctest examples to be run in an external process."""
    
    def __init__(self, source, want, exc_msg=None, lineno=0, indent=0,
                 options=None):
        # Parent constructor
        doctest.Example.__init__(self,source,want,exc_msg,lineno,indent,options)

        # An EXTRA newline is needed to prevent pexpect hangs
        self.source += '\n'

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

        # Whether to convert the input from ipython to python syntax
        ip2py = False
        # Find all doctest examples in the string.  First, try them as Python
        # examples, then as IPython ones
        terms = list(self._EXAMPLE_RE_PY.finditer(string))
        if terms:
            # Normal Python example
            Example = doctest.Example
        else:
            # It's an ipython example.  Note that IPExamples are run
            # in-process, so their syntax must be turned into valid python.
            # IPExternalExamples are run out-of-process (via pexpect) so they
            # don't need any filtering (a real ipython will be executing them).
            terms = list(self._EXAMPLE_RE_IP.finditer(string))
            if re.search(r'#\s*ipython-doctest:\s*EXTERNAL',string):
                Example = IPExternalExample
            else:
                Example = IPExample
                ip2py = True
        
        for m in terms:
            # Add the pre-example text to `output`.
            output.append(string[charno:m.start()])
            # Update lineno (lines before this example)
            lineno += string.count('\n', charno, m.start())
            # Extract info from the regexp match.
            (source, options, want, exc_msg) = \
                     self._parse_example(m, name, lineno,ip2py)
            if Example is IPExternalExample:
                options[doctest.NORMALIZE_WHITESPACE] = True
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

    def _parse_example(self, m, name, lineno,ip2py=False):
        """
        Given a regular expression match from `_EXAMPLE_RE` (`m`),
        return a pair `(source, want)`, where `source` is the matched
        example's source code (with prompts and indentation stripped);
        and `want` is the example's expected output (with indentation
        stripped).

        `name` is the string's name, and `lineno` is the line number
        where the example starts; both are used for error messages.

        Optional:
        `ip2py`: if true, filter the input via IPython to convert the syntax
        into valid python.
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

        if ip2py:
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


SKIP = register_optionflag('SKIP')

class IPDocTestRunner(doctest.DocTestRunner):
    """Modified DocTestRunner which can also run IPython tests.

    This runner is capable of handling IPython doctests that require
    out-of-process output capture (such as system calls via !cmd or aliases).
    Note however that because these tests are run in a separate process, many
    of doctest's fancier capabilities (such as detailed exception analysis) are
    not available.  So try to limit such tests to simple cases of matching
    actual output.
    """
    
    #/////////////////////////////////////////////////////////////////
    # DocTest Running
    #/////////////////////////////////////////////////////////////////

    def _run_iptest(self, test, out):
        """
        Run the examples in `test`.  Write the outcome of each example with one
        of the `DocTestRunner.report_*` methods, using the writer function
        `out`.  Return a tuple `(f, t)`, where `t` is the number of examples
        tried, and `f` is the number of examples that failed.  The examples are
        run in the namespace `test.globs`.

        IPython note: this is a modified version of the original __run()
        private method to handle out-of-process examples.
        """

        if out is None:
            out = sys.stdout.write

        # Keep track of the number of failures and tries.
        failures = tries = 0

        # Save the option flags (since option directives can be used
        # to modify them).
        original_optionflags = self.optionflags

        SUCCESS, FAILURE, BOOM = range(3) # `outcome` state

        check = self._checker.check_output

        # Process each example.
        for examplenum, example in enumerate(test.examples):

            # If REPORT_ONLY_FIRST_FAILURE is set, then supress
            # reporting after the first failure.
            quiet = (self.optionflags & REPORT_ONLY_FIRST_FAILURE and
                     failures > 0)

            # Merge in the example's options.
            self.optionflags = original_optionflags
            if example.options:
                for (optionflag, val) in example.options.items():
                    if val:
                        self.optionflags |= optionflag
                    else:
                        self.optionflags &= ~optionflag

            # If 'SKIP' is set, then skip this example.
            if self.optionflags & SKIP:
                continue

            # Record that we started this example.
            tries += 1
            if not quiet:
                self.report_start(out, test, example)

            # Run the example in the given context (globs), and record
            # any exception that gets raised.  (But don't intercept
            # keyboard interrupts.)
            try:
                # Don't blink!  This is where the user's code gets run.
                got = ''
                # The code is run in an external process
                got = iprunner.run_source(example.source,get_output=True)
            except KeyboardInterrupt:
                raise
            except:
                self.debugger.set_continue() # ==== Example Finished ====

            outcome = FAILURE   # guilty until proved innocent or insane

            if check(example.want, got, self.optionflags):
                outcome = SUCCESS

            # Report the outcome.
            if outcome is SUCCESS:
                if not quiet:
                    self.report_success(out, test, example, got)
            elif outcome is FAILURE:
                if not quiet:
                    self.report_failure(out, test, example, got)
                failures += 1
            elif outcome is BOOM:
                if not quiet:
                    self.report_unexpected_exception(out, test, example,
                                                     exc_info)
                failures += 1
            else:
                assert False, ("unknown outcome", outcome)

        # Restore the option flags (in case they were modified)
        self.optionflags = original_optionflags

        # Record and return the number of failures and tries.

        # Hack to access a parent private method by working around Python's
        # name mangling (which is fortunately simple).
        doctest.DocTestRunner._DocTestRunner__record_outcome(self,test,
                                                             failures, tries)
        return failures, tries

    def run(self, test, compileflags=None, out=None, clear_globs=True):
        """Run examples in `test`.

        This method will defer to the parent for normal Python examples, but it
        will run IPython ones via pexpect.
        """
        if not test.examples:
            return
        
        if isinstance(test.examples[0],IPExternalExample):
            self._run_iptest(test,out)
        else:
            DocTestRunner.run(self,test,compileflags,out,clear_globs)

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

def makeTestSuite(module_name,dt_module=None):
    """Make a TestSuite object for a given module, specified by name.

    This extracts all the doctests associated with a module using an
    IPDocTestLoader object.

    :Parameters:

      - module_name: a string containing the name of a module with unittests.

    :Keywords:

      - `dt_module` : string
        Name of a module to be scanned for doctests in docstrings.
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

    runner = IPDocTestRunner()

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

    def ipfunc2():
        """
        Tests that must be run in an external process


        # ipython-doctest: EXTERNAL

        In [11]: for i in range(10):
           ....:     print i,
           ....:     print i+1,
           ....:
        0 1 1 2 2 3 3 4 4 5 5 6 6 7 7 8 8 9 9 10


        In [1]: import os

        In [1]: print "hello"
        hello
        
        In [19]: cd /tmp
        /tmp

        In [20]: mkdir foo_ipython2

        In [21]: cd foo_ipython2
        /tmp/foo_ipython2

        In [23]: !touch bar baz

        In [24]: ls
        bar  baz

        In [24]: !ls
        bar  baz

        In [25]: cd /tmp
        /tmp

        In [26]: rm -rf foo_ipython2
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
