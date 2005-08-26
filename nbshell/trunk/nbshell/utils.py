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
    assert callable(func)
    try:
        res = func()
    except:
        res = default
    return res

def ifelse(expr1, expr2, expr3):
    """If expr1 is True returns expr2, else returns expr3. If expr2 and expr3
    are callables, calculates expr2() and expr3() and returns their values
    instead. The advantage of the second type of parameters is than only one of expr2() and expr3()
    will be evaluated, so for example:
    ifelse(len(a)>0, lambda:a[0], -1) will not throw an exception"""
    if expr1:
        #This ensures that ifelse(1, lambda:None, lambda:2) will return None, not 2
        return (callable(expr2) and (expr2(),) or (expr2,))[0]
    else:
        return (callable(expr3) and (expr3(),) or (expr3,))[0]

def accumulate(function, sequence, start = None, end = None):
    """'function' is a two parameter function. Returns

    func(func(...func(seq[0],seq[1]),seq[2])...) 
    
    or

    func(func(...func(start, seq[0]),seq[1]),...)

    if start is not None. If end is not None stops calling the function when
    its result equals end and returns end"""
    
    it = iter(sequence)
    if start is None:
        start = it.next()
        
    result = function(start, it.next())
    for elem in it:
        if end is not None and result == end:
            return result
        result = function(result, elem)
    return result


#functions for testing
def match_all(function, sequence):
    """Applies function on each element in the list. Returns True if all the
    results were True"""
    return len(filter(lambda x: not function(x), sequence)) == 0

def match_equal(function, sequence, number):
    """Returns True if exactly number matches occured"""
    return len(filter(function, sequence)) == number

def match_less_than(function, sequence, number):
    """Returns True if less than number matches occured"""
    return len(filter(function, sequence)) < number

def match_more_than(function, sequence, number):
    """Returns True if more than number matches occured"""
    return len(filter(function, sequence)) > number

#def multiple_match(functions, sequence):
#    """ 'functions' is a list. Returns True if each element in the sequence was ma
#Functions for testing lxml Elements
def match_subelement(element, function):
    """Returns true if the function applied to a child of the element returns
    True for some element"""
    return match_more_than(function, element.getchildren(), 0)

def match_one_subelement(element, function):
    """Returns True if there is exactly one subelement which is matched by the
    function"""
    return match_equal(function, element.getchildren(), 1)

def test_subelements(element, dict, default = lambda x:False):
    """Returns True if for each subelement x of element, either the tag is in
    dict.keys() and dict[x.tag](x) == True or the tag is not in dict.keys()
    and default(x) returns True"""
    
    return match_all(lambda x: ifelse(x.tag in dict.keys(),
                                      lambda:dict[x.tag](x),
                                      lambda:default(x)),
                   element.getchildren())
