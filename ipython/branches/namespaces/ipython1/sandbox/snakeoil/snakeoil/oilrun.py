"""Test running support for the SnakeOil package."""

__docformat__ = "restructuredtext en"

# Stdlib module imports
import doctest
import glob
import os
import sys
import time
import unittest

from optparse import OptionParser

# From our own package
import oilutil, oilscript
from oildoc import DocTestLoader

# From ipython, for interactive debugging
from IPython.Shell import IPShellEmbed
ipshell = IPShellEmbed(['-xmode','Verbose'])

# Code begins

def get_test_suites(verbosity=1):
    """Return all the testSuite values from all collected test suites in the
    testing directory."""

    suites = []
    dt_files = []

    # Build a list of all the module names to load
    testpat = 'test_*.py'
    mod_names = [os.path.basename(f).replace('.py','')
                 for f in glob.glob(testpat)
                 if '_doctest' not in f]
    
    mod_names.sort()

    # DBG - manually select certain tests:
    #mod_names = ['test_key']  # dbg
    
    if verbosity > 1:
        print 'Module names to search:',mod_names

    # Extract the testSuite variable from each loaded module.  First, make
    # sure we get them from own path, regardless of where the user is running
    # this
    try:
        sys.path.insert(0,oilutil.TEST_PATH)
        for mname in mod_names:
            if verbosity > 1:
                print '* snakeoil - importing module:',mname
            mod = __import__(mname)
            mod_suite,mod_dtf = mod.testSuite(False)
            suites.append(mod_suite)
            if mod_dtf:
                dt_files.extend(mod_dtf)
    finally:
        # Restore sys.path
        sys.path.pop(0)
    return suites,dt_files


def run_ut_suites(suites,verbosity):
    """Run one or more unittest suites."""
    testRunner = unittest.TextTestRunner(verbosity=verbosity)
    result = testRunner.run(unittest.TestSuite(suites))
    ut_run = result.testsRun
    ut_failed, ut_errored = map(len, (result.failures, result.errors))
    return result, ut_run, ut_failed, ut_errored


def run_doctest_file(dtf,verbosity,debug):
    """Run a single doctest file.

    :Parameters:
      dtf : path
        A test filename.  This must contain valid input for doctest.testfile().

      verbosity : int
        Level of verbosity for the doctest run.

      debug : bool
        If true, any errors or failures in a doctest file will raise
        immediately an exception.  For errors, the interactive debugger from an
        embedded IPython shell will activate in post-mortem mode, while for
        failures, a real IPython will open up in the namespace where the
        failure occured.

    :Return:
      nf,nt: number of tests failed and total tests run.
    """
    dt_verb = max(0,verbosity-1)
    try:
        nf,nt = doctest.testfile(dtf,report=0,verbose=dt_verb,
                                 raise_on_error=debug,
                                 module_relative=False)
    # We only get to handle the exceptions ourselves if debug was true,
    # since otherwise doctest swallows them and leaves them for the summary
    # report at the end.
    except doctest.UnexpectedException,failure:
        # We don't really know how many tests ran, but at least let's make
        # sure we report a failure
        nf = nt = 1
        try:
            exc_info = failure.exc_info
            raise exc_info[0], exc_info[1], exc_info[2]
        except:
            print '#'*80
            print '*** ERROR in doctest ***'
            print 'File <%s>, line: %s' % (failure.test.filename,
                                         failure.example.lineno)
            print 'Source:\n',failure.example.source
            ipshell.IP.showtraceback()
            print 'Entering debugger:'
            ipshell.IP.debugger(force=True)
    except doctest.DocTestFailure,failure:
        # We don't really know how many tests ran, but at least let's make
        # sure we report a failure
        nf = nt = 1
        print '#'*80
        print '*** FAILURE in doctest ***'
        print 'File <%s>, line: %s' % (failure.test.filename,
                                       failure.example.lineno)
        print 'Test source:\n',failure.example.source
        print 'Test Wanted:\n',failure.example.want
        print 'Test got:\n',failure.got
        ipshell('Entering IPython inside test namespace:',
                failure.test.globs)

    return nf,nt


def run_doctests(tf,verbosity,debug):
    """Run a set of doctests.

    :Parameters:
      tf : list
        A list of test filenames.  These must contain valid input for
      doctest.testfile().

      verbosity : int
        Level of verbosity for the doctest run.

      debug : bool
        If true, any errors or failures in a doctest file will raise
        immediately an exception.  For errors, the interactive debugger from an
        embedded IPython shell will activate in post-mortem mode, while for
        failures, a real IPython will open up in the namespace where the
        failure occured.

    :Return:
      nf,nt: number of tests failed and total tests run.
    """
    dt_run,dt_failed = 0,0
    dt_verb = max(0,verbosity-1)
    startTime = time.time()
    for dtf in tf:
        nf,nt = run_doctest_file(dtf,verbosity,debug)
        dt_run += nt
        dt_failed += nf
    timeTaken = time.time() - startTime

    if doctest.master:
        doctest.master.summarize(verbose=dt_verb)
    print ("Ran %d doctest%s in %.3fs" %
           (dt_run, dt_run != 1 and "s" or "", timeTaken))
    if dt_failed:
        print 'FAILED Doctests:',dt_failed

    return dt_failed,dt_run


def all_tests_summary(result,ut_info,dt_info):
    """Return a summary of the results of a TestSuite run.

    :Parameters:
      result : TestResult instance.

      ut_info : 3-element tuple
        This 

    :Returns:
      A string with the summary information.
    """

    ut_run,ut_failed,ut_errored = ut_info
    dt_failed,dt_run = dt_info

    # Summarize everything
    out = []
    out.append('*'*80)
    out.append('             Run   Fail    Error')
    out.append('Unittests     %s     %s        %s' % \
               (ut_run,ut_failed,ut_errored))

    out.append('Doctests      %s     %s ' % (dt_run,dt_failed))
    out.append('')
    out.append('Total         %s     %s        %s ' % 
               (ut_run+dt_run,ut_failed+dt_failed,ut_errored))
    out.append('')
    out.append('Final status: ')
    if result.wasSuccessful() and dt_failed == 0:
        out[-1] += 'OK'
    else:
        out[-1] += '* FAILED *'

    return '\n'.join(out)

def run_all_tests(suites,dt_files,verbosity=1,debug=False):
    """Run all tests, combining unittests and doctests."""

    # Unittest part
    print '*'*80
    print 'Running unittests...'
    result, ut_run, ut_failed, ut_errored = run_ut_suites(suites,verbosity)
    
    # Doctest part
    print '*'*80
    print 'Running doctests...'
    dt_failed,dt_run = run_doctests(dt_files,verbosity,debug)

    # Summarize everything
    print all_tests_summary(result,(ut_run,ut_failed,ut_errored),
                            (dt_failed,dt_run))


def make_test_suite(module_name,dt_files=None,dt_modules=None,t_scripts=None,
                    idt=True):
    """Make a TestSuite object for a given module, specified by name.

    This extracts all the doctests associated with a module using a
    DocTestLoader object.

    :Parameters:

      - module_name: a string containing the name of a module with unittests.

    :Keywords:

      dt_files : list of strings
        List of names of plain text files to be treated as doctests.

      dt_modules : list of strings
        List of names of modules to be scanned for doctests in docstrings.

      t_scripts : list of strings
        List of names scripts to be converted into unittests via oilscript.

      idt : bool (True)
        If True, return integrated doctests.  This means that each filename
        listed in dt_files is turned into a *single* unittest, suitable for
        running via unittest's runner or Twisted's Trial runner.  If false, the
        dt_files parameter is returned unmodified, so that other test runners
        (such as oilrun) can run the doctests with finer granularity.
    """

    mod = oilutil.my_import(module_name)
    if idt:
        suite = DocTestLoader(dt_files,dt_modules).loadTestsFromModule(mod)
    else:
        suite = DocTestLoader(None,dt_modules).loadTestsFromModule(mod)
        
    if t_scripts is not None:
        suite.addTest(oilscript.make_test_suite(
            *oilutil.list_strings(t_scripts)))
    if idt:
        return suite
    else:
        return suite,dt_files

##############################################################################
# Functionality for use as a command-line script
oilrun_usage = \
"""Global test runner for the SnakeOil package.

    %prog [options] [file1 file2...]


Description
===========
By default, this driver looks for all files of the form

test_*.py

in the current directory, which DON'T have _doctest in their name.  It then
imports each as a module, and extracts from it the variable

mod.testSuite

which should be a unittest.TestSuite instance.  These test suites get
aggregated and run together.

To add a new set of tests, the only requirements are then:

1. Name it test_SOMETHING.py

2. Inside, define a function named exactly testSuite that returns a test suite.

The testTEMPLATE.py script can be used as a starting point.


Arguments
=========

If filenames are given as arguments, they should contain valid doctest
content.  In that case, they are run as doctests only.
"""

def mkparser():
    "Parse command line and return the parser object"

    parser = OptionParser(usage=oilrun_usage)
    newopt = parser.add_option

    newopt('-v','--verbosity',default=1,type=int,
           help='Verbosity level: 0->quiet, 2->loud')

    newopt('-d','--debug',action='store_true',default=False,
           help='Debug mode (fires interactive debugger in doctests')

    return parser


def main0(argv=None,tests=None):
    """If run as a standalone script, provide minimally usable
    functionality

    :Keywords:
      argv : list (None)
        List of arguments for option parsing, defaults to sys.argv[1:]

      tests : tuple (None)
        If given, a pair of (suites,doctest_filenames).  suites must be a
        TestSuite object, while doctest_filenames must be a list of filenames
        to load as doctests."""

    parser = mkparser()
    opts,args = parser.parse_args(argv)
    if tests is None:
        suites,dt_files = get_test_suites(opts.verbosity)
    else:
        suites,dt_files = tests
    run_all_tests(suites,dt_files,opts.verbosity,opts.debug)
        
def main(argv=None,tests=None):
    """If run as a standalone script, provide minimally usable
    functionality

    :Keywords:
      argv : list (None)
        List of arguments for option parsing, defaults to sys.argv[1:]

      tests : tuple (None)
        If given, a pair of (suites,doctest_filenames).  suites must be a
        TestSuite object, while doctest_filenames must be a list of filenames
        to load as doctests."""

    parser = mkparser()
    opts,args = parser.parse_args(argv)
    run_doctests(args,opts.verbosity,opts.debug)
        

if __name__ == '__main__':
    main()
