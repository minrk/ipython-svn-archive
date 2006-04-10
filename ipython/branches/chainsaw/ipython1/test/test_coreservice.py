"""This file contains unittests for the coreservice.py module.

Things that should be tested:
- Should the CoreService return Deferred objects?
- Run the same tests that are run in shell.py.
- Make sure that the Interface is really implemented.
- The startService and stopService methods.
"""

from twisted.trial import unittest

from ipython1.kernel import coreservice, corepb

class FirstTest(unittest.TestCase):

    _execute = [(0,"a = 5","",""),
        (1,"b = 10","",""),
        (2,"c = a + b","",""),
        (3,"print c","15\n","")]

    def setUp(self):
        self.ipcore = coreservice.CoreService()
        self.ipcore.startService()
        
    def tearDown(self):
        self.ipcore.stopService()
        
    def testMy(self):
        self.assertEquals(1,1)