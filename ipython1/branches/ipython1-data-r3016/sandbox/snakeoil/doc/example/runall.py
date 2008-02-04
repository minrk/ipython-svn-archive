#!/usr/bin/env python
"""Run all examples for SnakeOil"""

# needed modules
import sys
import os

from snakeoil import oilscript, oilrun, oildoc

# code begins
def xsys(cmd,exit_values=None):
    """Wrapper around os.system that stops if cmd errors out.

    :Keywords:
      exit_values : list

        A list of values to use as triggers to exit the program.  If not given,
        then any non-zero exit value forces an exit.  This allows you to not
        exit on programs that signal non-fatal errors via their exit status.
        """

    stat = os.system(cmd)
    exit = False
    if exit_values is None:
        if stat:
            exit = True
    else:
        if stat in exit_values:
            exit = True

    if exit:
        print >> sys.stderr,"*** ERROR ***"
        print >> sys.stderr,"Command:",cmd
        print >> sys.stderr,"Exited with status:",stat
        print >> sys.stderr,"Aborting."
        sys.exit(stat)


if __name__=='__main__':

    # Generate doctest files out of python sources
    xsys('py2doctest -f pydt.py')
    xsys('py2doctest -f -t "#-# " pydt2.py')

    # Generate doctest files out of reST templates that include Python
    xsys('mkdoctest -f pydt3.tpl.txt')

    # Make HTML versions of all the doctests for documentation.  Don't fail if
    # the user doesn't have rst2html installed (the emtpy [] does that)
    xsys('rst2html pydt.txt pydt.html',[])
    xsys('rst2html pydt2.txt pydt2.html',[])
    xsys('rst2html pydt3.txt pydt3.html',[])

    # Run standalone scripts by themselves
    print
    print '>-<'*25
    print 'Standalone scripts, run independently'
    xsys('./uscriptex.py')
    xsys('./uscriptex2.py')

    # Run these same scripts
    print
    print '>-<'*25
    print 'Standalone scripts, run via oilscript'
    oilscript.main(['uscriptex.py','uscriptex2.py'])

    # Call a test_X.py file that describes and aggregates multiple tests
    print
    print '>-<'*25
    print 'test_example.py script, that aggregates tests'
    xsys('./test_example.py')

    # And finally call the oilrun test runner that should collect all the
    # test_X.py files in the directory.
    print
    print '>-<'*25
    print 'SnakeOil automatic runner:'
    oilrun.main([])
