"""This file contains unittests for the shell.py module.

Things that should be tested:
- Methods should return XML-RPC/PB friendly things (no None allowed)
- Each interface method should be tested thoroughly
- Don't worry about implementation methods
"""

from twisted.trial import unittest
from ipython1.core import shell
from ipython1.kernel1p.kernelerror import NotDefined

class BasicShellTest(unittest.TestCase):

    def setUp(self):
        self.s = shell.InteractiveShell()
        
    def testExecute(self):
        commands = [(0,"a = 5","",""),
            (1,"b = 10","",""),
            (2,"c = a + b","",""),
            (3,"print c","15\n",""),
            (4,"import math","",""),
            (5,"2.0*math.pi","6.2831853071795862\n","")]
        for c in commands:
            result = self.s.execute(c[1])
            self.assertEquals(result, c)
            
    def testPutGet(self):
        objs = [10,"hi there",1.2342354,{"p":(1,2)}]
        for o in objs:
            self.s.put("key",o)
            value = self.s.get("key")
            self.assertEquals(value,o)
        self.assertRaises(TypeError,self.s.put,10)
        self.assertRaises(TypeError,self.s.get,10)
        self.s.reset()
        self.assert_(isinstance(self.s.get("a"),NotDefined))
        
    def testUpdate(self):
        d = {"a": 10, "b": 34.3434, "c": "hi there"}
        self.s.update(d)
        for k in d.keys():
            value = self.s.get(k)
            self.assertEquals(value, d[k])
        self.assertRaises(TypeError, self.s.update, [1,2,2])
        
    def testCommand(self):
        self.assertRaises(IndexError,self.s.get_command)
        self.s.execute("a = 5")
        self.assertEquals(self.s.get_command(),(0,"a = 5","",""))
        self.assertEquals(self.s.get_command(0),(0,"a = 5","",""))
        self.s.reset()
        self.assertEquals(self.s.get_last_command_index(),-1)
        self.assertRaises(IndexError,self.s.get_command)
        
        