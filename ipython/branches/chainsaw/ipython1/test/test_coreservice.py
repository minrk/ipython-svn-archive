
from twisted.trial import unittest

from ipython1.kernel import coreservice, corepb

class FirstTest(unittest.TestCase):

    def setUp(self):
        self.ipcore = coreservice.CoreService()
        self.ipcore.startService()
        
    def tearDown(self):
        selff.ipcore.stopService
        
    def testExecute(self):
        d = self.ipcore.execute("a = 5")
        d.addCallback(self._checkExecute)
        return d
        
    def _checkExecute(self, result):
        self.assertEquals(result, (0,"a = 5","",""))