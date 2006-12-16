"""Utilities for testing code.

Part of the mwadap library."""

# Required modules and packages

# Standard Python lib
import doctest
import os
import sets
import sys
import unittest

# From this project

# path to our own installation, so we can find source files under this.
TEST_PATH = os.path.dirname(os.path.abspath(__file__))

# Global flag, used by vprint
VERBOSE = '-v' in sys.argv or '--verbose' in sys.argv

##########################################################################
# Code begins

class DocTestLoader(unittest.TestLoader):
    """A test loader with doctest support.

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

class IPDocTestParser(doctest.DocTestParser):
    """
    A class used to parse strings containing doctest examples.
    """
    # This regular expression is used to find doctest examples in a
    # string.  It defines three groups: `source` is the source code
    # (including leading indentation and prompts); `indent` is the
    # indentation of the first (PS1) line of the source code; and
    # `want` is the expected output (including leading indentation).
    _EXAMPLE_RE = re.compile(r'''
        # Source consists of a PS1 line followed by zero or more PS2 lines.
        (?P<source>
            (?:^(?P<indent> [ ]*) >>>    .*)    # PS1 line
            (?:\n           [ ]*  \.\.\. .*)*)  # PS2 lines
        \n?
        # Want consists of any non-blank lines that do not start with PS1.
        (?P<want> (?:(?![ ]*$)    # Not a blank line
                     (?![ ]*>>>)  # Not a line starting with PS1
                     .*$\n?       # But any other line
                  )*)
        ''', re.MULTILINE | re.VERBOSE)


def makeTestSuite(module_name,module=None):
    """Make a TestSuite object for a given module, specified by name.

    This extracts all the doctests associated with a module using a
    DocTestLoader object.

    Inputs:

      - module_name: a string containing 
    Optional inputs:
    """

    mod = __import__(module_name)
    return DocTestLoader(dt_module=module).loadTestsFromModule(mod)

# Some utility functions
def vprint(*args):
    """Print-like function which relies on a global VERBOSE flag."""
    if not VERBOSE:
        return

    write = sys.stdout.write
    for item in args:
        write(str(item))
    write('\n')
    sys.stdout.flush()

def test_path(path):
    """Return a path as a subdir of the test package.

    This finds the correct path of the test package on disk, and prepends it
    to the input path."""
    
    return os.path.join(TEST_PATH,path)
