""" tester.py - Code for testing nbshell """

import os
import sys
import unittest

import wx

from nbshell.utils import *

def print_on_false(expr, text):
    """Returns the value of expr. If expr == False, prints the text on
    sys.stderr"""
    if expr:
        return True
    else:
        print >>sys.stderr, text
        return False
    
#functions for testing the notebook format. NBDOC: They should go to nbdoc
def test_notebook(elem):
    """ Tests if the element is a notebook"""
    return print_on_false(\
        elem.tag == 'notebook' and len(elem.attrib) == 0 and\
        test_subelements(elem, #Test subelements
                         {'head' : test_head,  
                          'ipython-log' : test_ipython_log,
                          'sheet' : test_sheet}) and\
        len(elem.findall('sheet')) == 1#There must be only one sheet
        ,'TESTING: Wrong notebook')
        

def test_head(elem):
    #TODO: fix this
    return print_on_false(elem.tag == 'head', 'TESTING: Wrong head')

def test_ipython_log(elem):
    """Tests for ipython-log elements"""
    #TODO: Add tests to check if the numbering of the cells is correct, i.e.
    #all cells have unique numbers
    return print_on_false(
        elem.tag == 'ipython-log' and
        (len(elem.attrib) == 0 or #Test the attributes
         len(elem.attrib) == 1 and
         elem.attrib.get('id', None) is not None) and
        test_subelements(elem, #Test subelements
                         {'cell' : test_cell})
        , 'TESTING: Wrong ipython-log')
        


def test_cell(elem):
    #etree.dump(elem) #dbg
    tags = ['input', 'special-input', 'output', 'stdout', 'stderr', 'traceback']
    children = elem.getchildren()
    return print_on_false(
        (elem.tag == 'cell' and\
         #Test attributes. There is only one attribute
         len(elem.attrib) == 1 and\
         #Its name is 'number' and it is a natural number
         elem.attrib.get('number','').isdigit() and\
         #Test subelements
         match_all(lambda x:\
                   (x.tag in tags and\
                    #The element has no attributes
                    len(x.attrib) == 0 and\
                    #The element has no subelements
                    len(x) == 0 and\
                    #The first and the last characters of the text are newlines
                    len(x.text)>=2 and x.text[0] == '\n' and x.text[-1] == '\n'),\
                   children) and\
         #There must be at most one of each kind of subelement
         match_all(lambda tag: len(elem.findall(tag)) <= 1, tags) and\
         #There must be at least one input or special-input
         len(elem.findall('input') + elem.findall('special-input')) >= 1)\
        , 'TESTING: Wrong cell')

def test_sheet(elem):
    """ Tests if the parameter is a correct sheet element"""
    return print_on_false(\
        elem.tag == 'sheet' and len(elem.attrib) == 0 and\
        test_subelements(elem, {'ipython-block'  : test_ipython_block,\
                                'ipython-figure' : test_ipython_figure},
                         default = lambda x:True) #TODO: check the rest of the sheet
        , 'TESTING: Wrong sheet')

def test_ipython_block(elem):
    """ Tests if the parameter is a correct ipython-block element. Does not
    check if there is a log and cells corresponding to this element"""
    return print_on_false(\
        elem.tag == 'ipython-block' and len(elem.attrib) == 0 or\
        (len(elem.attrib) == 1 and elem.attrib.get('logid',None) != None) and\
        test_subelements(elem, {'ipython-cell':test_ipython_cell})\
        , 'TESTING: Wrong ipython-block')

def test_ipython_cell(elem):
    #TODO fix this
    return print_on_false(elem.tag == 'ipython-cell', 'TESTING: Wrong ipython-cell')

def test_ipython_figure(elem):
    #TODO: fix this
    return print_on_false(elem.tag == 'ipython-figure', 'TESTING: Wrong ipython-figure')
        

class SimpleTests(unittest.TestCase):
    """ Tests which do not require external input files"""
    
    def setUp(self):
        self.app = wx.GetApp()
        self.document = self.app.document
        self.logs = self.document.logs
        self.sheet = self.document.sheet
        self.frame = self.app.frame
        
    def tearDown(self):
        self.document.Clear()
        pass
    
    def testNew(self):
        """Tests the new method in the frame"""
        self.frame.OnNew()
        self.sheet.UpdateDoc()
        root = self.document.notebook.root
        #This is a notebook
        self.failUnless(test_notebook(root))
        #There is only one log
        self.failUnless(match_one_subelement(root, lambda x: x.tag =='ipython-log'))
        log = root.find('ipython-log')
        #The log has id='default-log'
        self.failUnless(log.attrib.get('id',None) == 'default-log')
        #The log has two cells, one with number == 0 and one with number == 1
        cells = log.findall('cell')
        self.failUnless(len(cells) == 2)
        self.failUnless(match_all(lambda x: x.attrib['number'] in ['0', '1'],\
                                  cells))
        #And so on. Testing stuff like this is very annoying

suite = unittest.TestSuite()
suite.addTest(SimpleTests('testNew'))

#class TestCase(unittest.TestCase):
    #"""Class TestCase. Used for testing nbshell"""
    
##    def __init__(self, runfunc):
##        print 'runfunc::::::::::::::::::::',str(runfunc)
##        unittest.TestCase.__init__(self,runfunc)
        
    #def setUp(self):
        ##TODO: this won't work if current directory is wrong
        #testdir = './nbshell/test/'
        #self.testdir = os.path.abspath(testdir)
        #self.tests = filter(lambda x:os.path.isdir(os.path.join(self.testdir,x)),
                       #os.listdir(self.testdir))
        #self.cwd = os.getcwdu()
            
    
    #def testTester(self):
        #"""Testing if the tester works"""
        #print >>sys.stderr, 'The tester works'
        #self.failIf(False)
        
    #def runTest(self):
        #for test in self.tests:
            #os.chdir(os.path.join(self.testdir, test))

            #namespace = {}
            #execfile(os.path.join(self.testdir,test,'test.py'), namespace)
            #for item in filter(lambda x: 
                               #len(x[0])>=4 and x[0][0:4] == 'test' and 
                               #callable(x[1]), namespace.items()):
                #item[1](self)
            #os.chdir(self.cwd)
