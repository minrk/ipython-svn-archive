"""Enhancements to doctest.
"""

__docformat__ = "restructuredtext en"

# Required modules and packages

# Standard Python lib
import doctest
import os
import re
import sys
import unittest

from optparse import OptionParser

# IPython-specific libraries
from IPython.genutils import fatal
from IPython.irunner import RunnerFactory

# From this project
import oilscript
from oilutil import IndentOut, my_import, list_strings


# Global defaults
TEXT_MARKER = '### '

#############################################################################
# Code begins

def writebuf(buf,write):
    """Write out and clear the input buffer with the given write method."""
    
    write(''.join(buf))
    buf [:] = []
    
def runbuf(buf,runner,write):
    """Run the input buffer as source.  The write method is needed to put in
    the proper reST code marks and needed whitespace."""
    
    source = ''.join(buf)
    if not source:
        return
    if source.isspace():
        write(source)
    else:
        write('::\n')
        if not buf[0].isspace():
            # Add a blank line before the start of verbatim input if the
            # original source didn't have it, to keep reST compilers happy.
            write('\n')
        runner.run_source(source)
        write('\n')
    buf [:] = []

def txt2doctest(infile,outfile):
    """Create a valid doctest file from the input.

    The input file is assumed to contain plain text and file inclusion
    directives of the form

    %run somefile.py

    These directives are used to run the named files.  These are executed via a
    separate Python process, and all input/output is recorded in the resulting
    output file.
    
    :Parameters:
      infile : open file-like object

      outfile : open file-like object
    """
    
    # all output from included files will be indented 
    indentOut = IndentOut(outfile,4)
    getRunner = RunnerFactory(indentOut)

    # Marker in reST for transition lines
    rst_transition = '\n'+'-'*76+'\n\n'

    # local shorthand for loop
    write = outfile.write

    # Process input, simply writing back out all normal lines and executing the
    # files in lines marked as '%run filename'.
    for line in infile:
        if line.startswith('%run '):
            # We don't support files with spaces in their names.
            incfname = line.split()[1]

            # We make the output of the included file appear bracketed between
            # clear reST transition marks, and indent it so that if anyone
            # makes an HTML or PDF out of the file, all doctest input and
            # output appears in proper literal blocks.
            write(rst_transition)
            write('Begin included file ``%s``::\n\n' % incfname)

            # I deliberately do NOT trap any exceptions here, so that if
            # there's any problem, the user running this at the command line
            # finds out immediately by the code blowing up, rather than ending
            # up silently with an incomplete or incorrect file.
            getRunner(incfname).run_file(incfname)

            write('\nEnd included file ``%s``\n' % incfname)
            write(rst_transition)
        else:
            # The rest of the input file is just written out
            write(line)


def py2doctest(infile,outfile,runner,text_marker=TEXT_MARKER):
    """Create a valid doctest file from the input.

    The input file is assumed to contain plain text and file inclusion
    directives of the form

    %run somefile.py

    These directives are used to run the named files.  These are executed via a
    separate Python process, and all input/output is recorded in the resulting
    output file.
    
    :Parameters:
      infile : open file-like object

      outfile : open file-like object
    """

    # Let's be nice and allow lines that have ONLY the text marker without the
    # right number of trailing spaces to be recognized as empty text lines.
    # Since you can't normally see if you have a trailing whitespace (and some
    # editors automatically strip it out), being too strict on expecting the
    # marker's whitespace to be present on empty lines is really an
    # inconvenience.
    text_mark_bare = text_marker.rstrip()
    
    # Process input.  This is basically a mini state machine with 2 states:
    # 'code' and 'text'.  As we detect a transition, we dump the accumulated
    # text from the previous state and start accumulating new state.
    CODE = 0
    TEXT = 1
    state = CODE
    buf = []

    # A few constants outside the for loop
    len_mark = len(text_marker)
    write = outfile.write

    # Actual input processing loop
    for line in infile:
        lstrip = line.rstrip()
        if line.startswith(text_marker) or lstrip == text_mark_bare:
            # Text mode: run accumulated code and start storing text input,
            # stripping the marker.
            #print 'TXT:<%r>' % line.rstrip()  # dbg
            if state == CODE:
                runbuf(buf,runner,write)
                state = TEXT
            if lstrip == text_mark_bare:
                buf.append('\n')
            else:
                buf.append(line[len_mark:])
        else:
            # Code mode: write out the accumulated text from the buffer, and
            # store code.
            if state == TEXT:
                writebuf(buf,write)
                state = CODE
            buf.append(line)

    # Flush final buffer
    if state == CODE:
        runbuf(buf,runner,write)
    else:
        writebuf(buf,write)


class DocTestLoader(unittest.TestLoader):
    """A test loader with doctest support.

    Instances of this loader will automatically add doctests found in a module
    to the test suite returned by the loadTestsFromModule method.  In addition,
    at initialization time a string of doctests can be given to the loader,
    enabling it to add doctests to a module which didn't have them in its
    docstring, coming from an external source."""

    def __init__(self,dt_files=None,dt_modules=None,test_finder=None):
        """Initialize the test loader.

        :Keywords:

          dt_files : list (None)
            List of names of files to be executed as doctests.
            
          dt_modules : list (None)
            List of module names to be scanned for doctests in their
            docstrings. 

          test_finder : instance (None)
            Instance of a testfinder (see doctest for details).
        """

        if dt_files is None: dt_files = []
        if dt_modules is None: dt_modules = []
        self.dt_files = list_strings(dt_files)
        self.dt_modules = list_strings(dt_modules)
        self.test_finder = test_finder

    def loadTestsFromModule(self, module):
        """Return a suite of all tests cases contained in the given module.

        If the loader was initialized with a doctests argument, then this
        string is assigned as the module's docstring."""

        # Start by loading any tests in the called module itself
        suite = super(self.__class__,self).loadTestsFromModule(module)

        # Now, load also tests referenced at construction time as companion
        # doctests that reside in standalone files
        for fname in self.dt_files:
            #print 'mod:',module  # dbg
            #print 'fname:',fname  # dbg
            suite.addTest(doctest.DocFileSuite(fname,module_relative=False))
        # Add docstring tests from module, if given at construction time
        for mod in self.dt_modules:
            suite.addTest(doctest.DocTestSuite(mod,
                                               test_finder=self.test_finder))

        return suite

##############################################################################
# Command-line usage as standalone programs for doctest generation
##############################################################################

#-----------------------------------------------------------------------------
# Expose the py2doctest facilities as a command-line program
#-----------------------------------------------------------------------------

py2doctest_usage = \
"""Utility for making a doctest file out of Python or IPython input.

  %prog [options] input_file [output_file]

This script is a convenient generator of doctest files that uses IPython's
irunner script to execute valid Python or IPython input in a separate process,
capture all of the output, and write it to an output file.

The input file, which should be a valid Python file, is fed to the separate
Python process for execution.  All input and output is saved to the output file
(or stdout if requested).  In addition, you can keep arbitrary text in
specially-marked comments that will be left verbatim (minus the comment marks)
in the output.  This allows you to write verbose commentary in your files for
the generation of the final doctest file.

The output file is valid reST, with the Python code indented four spaces and
'::' code marks put before any Python i/o block.  So if you use valid reST in
your marked text, the resulting file will all be valid reST, ready for
inclusion in auto-generated documentation, etc.


See the accompanying examples for input files with markup and the resulting
output. 

Notes
=====

For running any .txt file as a doctest, the following alias can be very
handy (in csh syntax, adapt to bash as needed):

alias doctest "python -c 'import sys,doctest;doctest.testfile(sys.argv[1])'"

You can even pass -v after the filename for verbose output."""


def mkparser_py2doctest():
    "Parse command line and return the parser object"

    parser = OptionParser(usage=py2doctest_usage)

    newopt = parser.add_option
    newopt('-f','--force',action='store_true',dest='force',default=False,
           help='Force overwriting of the output file.')
    newopt('-s','--stdout',action='store_true',dest='stdout',default=False,
           help='Use stdout instead of a file for output.')
    newopt('-t','--text_marker',type=str,default=TEXT_MARKER,
           help='String that marks a line as plain text in the code.\n'
           'It should be a valid comment, so it must start with #\n'
           'Default: %r' % TEXT_MARKER)

    return parser


def main_py2doctest():
    """Run as a script."""

    parser = mkparser_py2doctest()
    opts,args = parser.parse_args()

    #print 'opts:', opts  # dbg
    #print 'args:', args  # dbg

    # There's a stupid bug in optparse: for string values, it seems they
    # automatically escape '#' characters in the input.  Why, oh why???
    # Unescape them before actually keeping the marker since, well, we happen
    # to NEED the comment characters because text marks will pretty much ALWAYS
    # have '#' in them so the input can be valid python!
    text_marker = opts.text_marker.replace('\\#','#')

    # Input filename
    try:
        fname = args[0]
    except IndexError:
        parser.error("incorrect number of arguments")

    # Output filename
    try:
        outfname = args[1]
    except IndexError:
        bname, ext = os.path.splitext(fname)
        outfname = bname+'.txt'

    # Open input file
    infile = open(fname)

    # Now open the output file.  If opts.stdout was given, this overrides any
    # explicit choice of output filename and just directs all output to
    # stdout.
    if opts.stdout:
        outfile = sys.stdout
    else:
        # Argument processing finished, start main code
        if os.path.isfile(outfname) and not opts.force:
            fatal("Output file %r exists, use --force (-f) to overwrite."
                  % outfname)
        outfile = open(outfname,'w')

    # all python output will be indented 4 spaces
    indentOut = IndentOut(outfile,4)
    runner = RunnerFactory(indentOut)(fname)

    # Run the actual conversion code
    py2doctest(infile,outfile,runner,text_marker)

    # Cleanup
    infile.close()

    # Don't close sys.stdout!!!
    if outfile is not sys.stdout:
        outfile.close()


#-----------------------------------------------------------------------------
# Expose the mkdoctest facilities as a command-line program
#-----------------------------------------------------------------------------

MKDOCTEST_TPL = """
=========================
 Auto-generated doctests
=========================

This file was auto-generated by IPython in its entirety.  If you need finer
control over the contents, simply make a manual template.  See the
mkdoctest.py script for details.

%%run %s
"""

mkdoctest_usage = \
"""Utility for making a doctest file out of Python or IPython input.

  %prog [options] input_file [output_file]

This script is a convenient generator of doctest files that uses IPython's
irunner script to execute valid Python or IPython input in a separate process,
capture all of the output, and write it to an output file.

It can be used in one of two ways:

1. With a plain Python or IPython input file (denoted by extensions '.py' or
   '.ipy'.  In this case, the output is an auto-generated reST file with a
   basic header, and the captured Python input and output contained in an
   indented code block.

   If no output filename is given, the input name is used, with the extension
   replaced by '.txt'.

2. With an input template file.  Template files are simply plain text files
   with special directives of the form

   %run filename

   to include the named file at that point.

   If no output filename is given and the input filename is of the form
   'base.tpl.txt', the output will be automatically named 'base.txt'.
"""


def mkparser_mkdoctest():
    """Return a prepared options parser"""
    parser = OptionParser(usage=mkdoctest_usage)
    newopt = parser.add_option
    newopt('-f','--force',action='store_true',dest='force',default=False,
           help='Force overwriting of the output file.')
    newopt('-s','--stdout',action='store_true',dest='stdout',default=False,
           help='Use stdout instead of a file for output.')
    return parser


def main_mkdoctest():
    """Run as a script."""

    # Parse options and arguments.
    parser = mkparser_mkdoctest()
    opts,args = parser.parse_args()
    # Input filename
    try:
        fname = args[0]
    except IndexError:
        parser.error("incorrect number of arguments")

    # We auto-generate the output file based on a trivial template to make it
    # really easy to create simple doctests.
    auto_gen_output = False
    try:
        outfname = args[1]
    except IndexError:
        outfname = None

    if fname.endswith('.tpl.txt') and outfname is None:
        outfname = fname.replace('.tpl.txt','.txt')
    else:
        bname, ext = os.path.splitext(fname)
        if ext in ['.py','.ipy']:
            auto_gen_output = True
        if outfname is None:
            outfname = bname+'.txt'

    # Open input file

    # In auto-gen mode, we actually change the name of the input file to be our
    # auto-generated template
    if auto_gen_output:
        infile = tempfile.TemporaryFile()
        infile.write(MKDOCTEST_TPL % fname)
        infile.flush()
        infile.seek(0)
    else:
        infile = open(fname)

    # Now open the output file.  If opts.stdout was given, this overrides any
    # explicit choice of output filename and just directs all output to
    # stdout.
    if opts.stdout:
        outfile = sys.stdout
    else:
        # Argument processing finished, start main code
        if os.path.isfile(outfname) and not opts.force:
            fatal("Output file %r exists, use --force (-f) to overwrite."
                  % outfname)
        outfile = open(outfname,'w')

    # Run the actual conversion routine
    txt2doctest(infile,outfile)

    # Cleanup
    infile.close()

    # Don't close sys.stdout!!!
    if outfile is not sys.stdout:
        outfile.close()


# If called as a script, default to the py2doctest main routine
if __name__ == '__main__':
    main_py2doctest()
