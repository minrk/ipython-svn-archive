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
