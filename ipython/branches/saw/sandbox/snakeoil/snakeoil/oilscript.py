"""Support for running one or more standalone scripts as real unittests.
"""
__docformat__ = "restructuredtext en"

import new
import sys
import unittest

from optparse import OptionParser

# Optionally, offer a test object with numpy support.
try:
    from numpy import testing
    has_numpy = True
except ImportError:
    has_numpy = False

def wrap(func,testManager):
    """Decorator to wrap test methods.

    Wraps any function by coupling its call to results accounting.
    """
    def meth(self,*a,**k):
        try:
            func(*a,**k)
        except self.test.failureException:
            self.result.addFailure(self.test, self.test._exc_info())
            raise
        except:
            self.result.addError(self.test, self.test._exc_info())
            raise
        else:
            self.succeed()

    meth.__doc__ = func.__doc__
    return new.instancemethod(meth,testManager, testManager.__class__)


class ScriptTestManager(object):
    def __init__(self,result=None,test=None):
        """
        """
        
        if result is None:
            result = unittest.TestResult()
            result.startTest(self)

        self.result = result

        # names of methods that record failure or success in TestCase
        # instances.  We wrap them all with our results recording decorator.
        recmethods = ['assertAlmostEqual', 'assertAlmostEquals','assertEqual',
                      'assertEquals','assertFalse','assertNotAlmostEqual',
                      'assertNotAlmostEquals','assertNotEqual',
                      'assertNotEquals', 'assertRaises', 'assertTrue',
                      'assert_',
                      'fail','failIf','failIfAlmostEqual','failIfEqual',
                      'failUnless', 'failUnlessAlmostEqual', 'failUnlessEqual',
                      'failUnlessRaises', 'failureException']

        if test is None:
            # standalone 'script' mode: there is no outside test runner
            mode = 'script'
            test = unittest.FunctionTestCase(lambda *x,**k:None)
            self._rec_wrap(test,recmethods)
        else:
            # unittest mode, when run from inside an existing test runner
            mode = 'unittest'
            self._expose_from(test,recmethods)

        self.test = test
        self.mode = mode
        
    def _rec_wrap(self,test,recmethods):
        """Wrap a set of failure/assertion methods with results recording."""

        for methname in recmethods:
            setattr(self, methname, wrap(getattr(test,methname),self))

    def _expose_from(self,test,recmethods):
        """Expose the given list of methods from the given test instance.

        This simply exposes the underlying methods with no wrapping at all"""

        for methname in recmethods:
            setattr(self, methname, getattr(test,methname))

    def succeed(self):
        self.result.addSuccess(self)
        self.result.testsRun += 1

    def summary(self):
        """Return a summary string."""

        assert self.mode in ['script','unittest'],\
               "Invalid mode in test: %s" % self.mode
        
        if self.mode == 'unittest':
            # In this mode, there's no point in printing lots of stuff after
            # each script runs, that's the job of the test runner.
            return None
        
        return unittest_summary(self.result)

    def print_summary(self):
        """Print a summary string."""

        summ = self.summary()
        if summ is not None:
            print summ


if has_numpy:
    class NumpyScriptTestManager(ScriptTestManager):
        def __init__(self,result=None,test=None):
            ScriptTestManager.__init__(self,result=result,test=test)
            self._rec_wrap(testing,
                           ['assert_almost_equal','assert_approx_equal',
                            'assert_array_almost_equal',
                            'assert_array_equal','assert_array_less',
                            'assert_equal'])


class _TestManagerFactory(object):
    def __init__(self,manager_class):
        self.result = None
        self.test = None
        self.manager_class = manager_class
    
    def __call__(self,result=None,test=None):
        if result is None:
            result = self.result
        if test is None:
            test = self.test
        return self.manager_class(result,test)


# Declare the two publicly-useful factories
mkScriptTestManager = _TestManagerFactory(ScriptTestManager)
mkNumpyScriptTestManager = _TestManagerFactory(NumpyScriptTestManager)


class MyTextTestRunner(unittest.TextTestRunner):
    def _makeResult(self):
        return unittest._TextTestResult(self.stream, self.descriptions,
                                        self.verbosity)


class ScriptTestCase(unittest.FunctionTestCase):
    def run(self,result=None):
        #print '*** result:',result
        #print '*** run for method:',self._testMethodName  # dbg
        #print '***            doc:',self._testMethodDoc  # dbg

        if result is None: result = self.defaultTestResult()

        saved_manager_result = mkNumpyScriptTestManager.result
        saved_manager_test = mkNumpyScriptTestManager.test
        mkNumpyScriptTestManager.result = result
        mkNumpyScriptTestManager.test = self

        # XXX - HACK: because unittest had the bloody brilliant idea of using
        # private __attributes in its implementation, we have to work around
        # the name mangling in a subclass.
        self._testMethodName = '_FunctionTestCase__testFunc'

        try:
            super(ScriptTestCase,self).run(result)
        finally:
            mkNumpyScriptTestManager.result = saved_manager_result
            mkNumpyScriptTestManager.test = saved_manager_test
        #print  '--- result:',result  # dbg


def script2suite(fname):
    """Return a TestSuite from a filename"""

    suite =  unittest.TestSuite()

    test = ScriptTestCase(lambda : execfile(fname,{}))
    test.shortDescription = lambda : "Unittest script: %r" % fname

    suite.addTest(test)
    return suite

    
def make_test_suite(*fnames):
    """Make a unittest.TestSuite from one or more filenames"""
    
    return unittest.TestSuite(map(script2suite,fnames))


def unittest_summary(result):
    """Return a summary of the results of a TestSuite run.

    :Parameters:
      result : TestResult instance

    :Returns:
      A string with the summary information.
    """
    ut_run = result.testsRun
    ut_failed, ut_errored = map(len, (result.failures, result.errors))

    # Summarize everything
    out = []
    out.append('*'*80)
    out.append('             Run   Fail    Error')
    out.append('Unittests     %s     %s        %s' % \
               (ut_run,ut_failed,ut_errored))
    out.append('')
    out.append('Final status: ')
    if result.wasSuccessful():
        out[-1] += 'OK'
    else:
        out[-1] += '* FAILED *'
    return '\n'.join(out)

def runtests(fnames,verbosity=1,debug=False):
    """Run the actual tests"""
    
    print 'Running unittests...'
    suites = make_test_suite(*fnames)
    testRunner = MyTextTestRunner(verbosity=verbosity)
    result = testRunner.run(unittest.TestSuite(suites))
    print unittest_summary(result)

#############################################################################
# For usage as a standalone program
#############################################################################

oilscript_usage = \
"""Run one or more standalone python scripts as unit tests.

    %prog [options] [file1 file2...]
"""

def mkparser():
    """Return a prepared options parser"""
    parser = OptionParser(usage=oilscript_usage)
    newopt = parser.add_option

    newopt('-v','--verbosity',default=1,type=int,
           help='Verbosity level: 0->quiet, 2->loud')

    newopt('-d','--debug',action='store_true',default=False,
           help='Debug mode (fires interactive debugger in doctests')

    return parser


def main(argv=None):

    # Parse options and arguments.
    parser = mkparser()
    opts,args = parser.parse_args(argv)
    runtests(args,verbosity=opts.verbosity,debug=opts.debug)
    

if __name__ == '__main__':
    main()
