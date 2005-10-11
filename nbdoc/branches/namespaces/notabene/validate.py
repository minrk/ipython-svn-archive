#!/usr/bin/env python
"""Validate notebook files for correct XML syntax.

TODO: Implement a RelaxNG schema to validate notebook files for their content.
"""

from xml.parsers import expat
from cStringIO import StringIO

def _decorate(lines, startlineno, errlineno, errcolumn, errmsg):
    declines = ['%5s  %s' % (x, y) 
        for x, y in zip(xrange(startlineno, startlineno+len(lines)),
                        lines)]
    declines.insert(errlineno, ' '*(7+errcolumn-1) + ('^- %s\n' % errmsg)) 
    return ''.join(declines)

def _report(e, lines):
    errlines = lines[e.lineno-3:e.lineno+2]
    return _decorate(errlines, e.lineno-2, 3, e.offset,
                    expat.ErrorString(e.code))

def isclean_file(filename):
    """Test if a file is valid XML.
    """
    f = open(filename)
    try:
        text = f.read()
    finally:
        f.close()

    f = StringIO(text)
    lines = list(f)
    f.seek(0,0)
    
    parser = expat.ParserCreate()
    try:
        parser.ParseFile(f)
    except expat.ExpatError, e:
        print _report(e, lines)
        return False

    print 'No syntax errors.'
    return True

def check_errors(xmldata):
    """Check if a given string is valid XML.

    If invalid:
      Returns a string displaying the error.
    If valid:
      Returns None.
    """
    parser = expat.ParserCreate()
    try:
        parser.Parse(xmldata)
    except expat.ExpatError, e:
        return _report(e, xmldata.splitlines()) #should be lines somehow
    else:
        return None #no errors
    
        
if __name__ == '__main__':
    import sys
    isclean_file(sys.argv[1])

