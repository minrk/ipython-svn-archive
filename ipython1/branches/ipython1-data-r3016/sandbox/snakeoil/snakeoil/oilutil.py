"""Utilities for testing code."""

__docformat__ = "restructuredtext en"

# Required modules and packages

# Standard Python lib
import os
import re
import sys

# External packages

# From this project

# path to our own installation, so we can find source files under this.
TEST_PATH = os.path.dirname(os.path.abspath(__file__))

# Global flag, used by vprint
VERBOSE = '-v' in sys.argv or '--verbose' in sys.argv

##########################################################################
# Code begins

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


def list_strings(arg):
    """Always return a list of strings, given a string or list of strings
    as input.

    :Examples:

        >>> list_strings('A single string')
        ['A single string']

        >>> list_strings(['A single string in a list'])
        ['A single string in a list']

        >>> list_strings(['A','list','of','strings'])
        ['A', 'list', 'of', 'strings']
    """

    if isinstance(arg,basestring): return [arg]
    else: return arg

def my_import(name):
    """Module importer - taken from the python documentation.

    This function allows importing names with dots in them."""
    
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

class IndentOut(object):
    """A simple output stream that indents all output by a fixed amount.

    Instances of this class trap output to a given stream and first reformat it
    to indent every input line."""
    
    def __init__(self,out=sys.stdout,indent=4):
        """Create an indented writer.

        :Keywords:

        - `out` : stream (sys.stdout)
          Output stream to actually write to after indenting.

        - `indent` : int
          Number of spaces to indent every input line by.
        """
        
        self.indent_text = ' '*indent
        self.indent = re.compile('^',re.MULTILINE).sub
        self.out = out
        self._write = out.write
        self.buffer = []
        self._closed = False

    def write(self,data):
        """Write a string to the output stream."""

        if self._closed:
            raise ValueError('I/O operation on closed file')
        self.buffer.append(data)

    def flush(self):
        if self.buffer:
            data = ''.join(self.buffer)
            self.buffer[:] = []
            self._write(self.indent(self.indent_text,data))
        
    def close(self):
        self.flush()
        self._closed = True
