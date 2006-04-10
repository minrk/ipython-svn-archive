"""This file contains unittests for the shell.py module.

Things that should be tested:
- Methods should return XML-RPC/PB friendly things (no None allowed)
- Each interface method should be tested thoroughly
- Don't worry about implementation methods
"""

from twisted.trial import unittest
from ipython1.core import shell

class FirstTest(unittest.TestCase):

    def setUp(self):
        self.s = shell.InteractiveShell()
        
    def testExecute(self):
        result = self.s.execute("a = 5")
        self.assertEquals(result, (0,"a = 5","",""))