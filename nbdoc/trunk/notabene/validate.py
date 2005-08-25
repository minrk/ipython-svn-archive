#!/usr/local/bin/python2.4
"""in answer to http://projects.scipy.org/ipython/ipython/ticket/2

first the simple cleaning function from
http://projects.scipy.org/ipython/ipython/attachment/ticket/2/niceerrs.py
, but later actual validation components could come here too."""

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

def iscleanFile(filename):
    """used when this is run as an executable utility"""
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

    print "No syntax errors found!"
    return True

def check_errors(xmldata):
    """to be used by notebook objects to report usefully up to nbshell"""
    parser = expat.ParserCreate()
    try:
        parser.Parse(xmldata)
    except expat.ExpatError, e:
        return _report(e, xmldata) #should be lines somehow
    else:
        return None #no errors
    
        
if __name__ == '__main__':
    import sys
    iscleanFile(sys.argv[1])

