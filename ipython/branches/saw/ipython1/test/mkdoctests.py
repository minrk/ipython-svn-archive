#!/usr/bin/env python
"""Utility for making a doctest file out of a template.

  %prog [options] template_file [output_file]

This script ...
"""

# Standard library imports

import optparse
import os
import re
import sys

# IPython-specific libraries
from IPython import irunner
from IPython.genutils import fatal

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

class RunnerFactory(object):
    """Code runner factory.

    This class provides an IPython code runner, but enforces that only one
    runner is every instantiated.  The runner is created based on the extension
    of the first file to run, and it raises an exception if a runner is later
    requested for a different extension type.

    This ensures that we don't generate example files for doctest with a mix of
    python and ipython syntax.
    """

    def __init__(self,out=sys.stdout):
        """Instantiate a code runner."""
        
        self.out = out
        self.runner = None
        self.runnerClass = None

    def _makeRunner(self,runnerClass):
        self.runnerClass = runnerClass
        self.runner = runnerClass(out=self.out)
        return self.runner
          
    def __call__(self,fname):
        """Return a runner for the given filename."""

        if fname.endswith('.py'):
            runnerClass = irunner.PythonRunner
        elif fname.endswith('.ipy'):
            runnerClass = irunner.IPythonRunner
        else:
            raise ValueError('Unknown file type for Runner: %r' % fname)

        if self.runner is None:
            return self._makeRunner(runnerClass)
        else:
            if runnerClass==self.runnerClass:
                return self.runner
            else:
                e='A runner of type %r can not run file %r' % \
                   (self.runnerClass,fname)
                raise ValueError(e)
        
def main():
    """Run as a script."""

    # Parse options and arguments.
    parser = optparse.OptionParser(usage=__doc__)
    newopt = parser.add_option
    newopt('-f','--force',action='store_true',dest='force',default=False,
           help='Force overwriting of the output file.')

    opts,args = parser.parse_args()
    if len(args) != 1:
        parser.error("incorrect number of arguments")

    fname = args[0]
    if fname.endswith('.tpl.txt'):
        outfname = fname.replace('.tpl.txt','.txt')
    else:
        try:
            print 'args:',args
            outfname = args[1]
        except IndexError:
            parser.error("incorrect number of arguments")

    # Argument processing finished, start main code
    if os.path.isfile(outfname) and not opts.force:
        fatal("Output file %r exists, use --force (-f) to overwrite."
              % outfname)

    # open in/out files
    infile = open(fname)    
    outfile = open(outfname,'w')
    write = outfile.write

    # all output from included files will be indented 
    indentOut = IndentOut(outfile,4)
    getRunner = RunnerFactory(indentOut)

    # Marker in reST for transition lines
    rst_transition = '\n'+'-'*76+'\n\n'

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
            write('Begin included file %s::\n\n' % incfname)

            # I deliberately do NOT trap any exceptions here, so that if
            # there's any problem, the user running this at the command line
            # finds out immediately by the code blowing up, rather than ending
            # up silently with an incomplete or incorrect file.
            getRunner(incfname).run_file(incfname)

            write('\nEnd included file %s\n' % incfname)
            write(rst_transition)
        else:
            # The rest of the input file is just written out
            write(line)
    infile.close()
    outfile.close()

if __name__ == '__main__':
    main()
