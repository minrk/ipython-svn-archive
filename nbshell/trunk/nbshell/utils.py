""" Utility functions and classes """

#This method is temporary until notebook.py is fixed

#from notabene import notebook
#from notabene.notebook import *

#def get_sheet_tags(self, do_specials=False):
#    if do_specials and hasattr(self, 'special'):
#        yield ET.Element('ipython-special',
#            number=str(self.number))
#    else:
#        yield ET.Element('ipython-input',
#            number=str(self.number))
#    for tag in ('traceback', 'stdout', 'stderr', 'output'):
#        if hasattr(self, tag):
#            yield ET.Element('ipython-%s'%tag,
#                number=str(self.number))
#notebook.Cell.get_sheet_tags = get_sheet_tags
#del notebook

from lxml import etree 

def findnew(element, tag):
    """Tries to find the tag in the element. If there is no such element,
    creates one"""
    el = element.find(tag)
    if el is None:
        el = etree.SubElement(element, tag)
    return el

#TODO: ask the lxml guys if they can include the following functionality in
#lxml
def getindex(element,subelement):
    """Searches subelement in element. If found returns its index, if not
    returns None
    """
    
    for (i, elem) in enumerate(element):
        if elem is subelement:
            return i
    return None

def getiterator2(root):
    """Returns an iterator which for each subelement yields a tuple of all
    elements in the path from the root to the given subelement, excluding the
    root. The root element is not returned"""
    
    #Recursive generators, yummy :)
    for subelement in root:
        yield (subelement,)
        iter = getiterator2(subelement)
        for result in iter:
            yield (subelement,) + result
            
def default(func, default = None):
    """If func throws an exception returns default, else returns the result of
    the function"""
    try:
        res = func()
    except:
        res = default
    return res

def ifelse(expr1, expr2, expr3):
    """If expr1 is True returns expr2(), else returns expr3(). expr2 and expr3
    are functions. To use ifelse for regular expressions use:
        ifelse(expr1, lambda:expr2, lambda:expr3)"""
    #This ensures that ifelse(1, lambda:None, lambda:2) will return None, not 2
    #expr2 and expr
    return ((expr1) and (expr2(),) or (expr3(),))[0] 
