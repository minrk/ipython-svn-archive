""" tester.py - Code for testing nbshell """

import sys
import unittest

class TestCase(unittest.TestCase):
    """Class TestCase. Used for testing nbshell"""
    
#    def __init__(self, runfunc):
#        print 'runfunc::::::::::::::::::::',str(runfunc)
#        unittest.TestCase.__init__(self,runfunc)
        
    def setUp(self):
        print >>sys.stderr, '-'*70
        print >>sys.stderr, 'Testing nbshell'
        pass
    
    def testTester(self):
        """Testing if the tester works"""
        print >>sys.stderr, 'The tester works'
        self.failIf(False)
        
    def runTest(self):
        self.testTester()