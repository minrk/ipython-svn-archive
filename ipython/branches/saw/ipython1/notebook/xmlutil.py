# encoding: utf-8
# -*- test-case-name: ipython1.test.test_notebook_xmlutil -*-
"""The XML Representation of Notebook components
"""
__docformat__ = "restructuredtext en"
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelley <benjaminrk@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import zope.interface as zi
import StringIO, datetime, xml.etree.ElementTree as ET

from twisted.python import components

from ipython1.notebook import models, dbutil

#-------------------------------------------------------------------------------
# XML representations of notebooks
#-------------------------------------------------------------------------------
def indent(s, n):
    """indent a multi-line string `s`, `n` spaces"""
    addline = 0
    if s[-1] == '\n':
        s = s[:-1]
        addline=1
    s = " "*n+s.replace("\n", "\n"+" "*n)
    return s +'\n'*addline

tformat = "%Y-%m-%d %H:%M:%S"
class IXML(zi.Interface):
    """The class for adapting object to an XML string"""
    pass

def XMLNotebook(nb):
    """Return an XML representation of a notebook"""
    s  = "<dateCreated>%s</dateCreated>\n"%(nb.dateCreated.strftime(tformat))
    s += "<dateModified>%s</dateModified>\n"%(nb.dateModified.strftime(tformat))
    s += "<username>%s</username>\n"%(nb.user.username)
    s += "<email>%s</email>\n"%(nb.user.email)
    s += indent(IXML(nb.root), 2)
    return "<Notebook>\n"+indent(s,2)+"</Notebook>\n"
    s

def XMLCellBase(cell):
    """The base of an XML representation of a cell"""
    s  = "<comment>%s</comment>\n"%(cell.comment)
    s += "<dateCreated>%s</dateCreated>\n"%(cell.dateCreated.strftime(tformat))
    s += "<dateModified>%s</dateModified>\n"%(cell.dateModified.strftime(tformat))
    return s

def XMLMultiCell(mc):
    """Return an XML representation of a MultiCell"""
    s = "<title>%s</title>\n"%(mc.title)
    s += XMLCellBase(mc)
    for i in range(len(mc.children)):
        s += indent(IXML(mc[i]), 2)
    return "<MultiCell>\n"+indent(s,2)+"</MultiCell>\n"

def XMLTextCell(cell):
    s  = XMLCellBase(cell)
    s += "<textData>%s</textData>\n"%(cell.textData)
    return "<TextCell>\n"+indent(s,2)+"</TextCell>\n"

def XMLInputCell(cell):
    s  = XMLCellBase(cell)
    s += "<input>%s</input>\n"%(cell.input)
    s += "<output>%s</output>\n"%(cell.output)
    return "<InputCell>\n"+indent(s,2)+"</InputCell>\n"
    


# components.registerAdapter(XMLNotebook, models.INotebook, IXML)
# components.registerAdapter(XMLMultiCell, models.IMultiCell, IXML)
# components.registerAdapter(XMLTextCell, models.ITextCell, IXML)
# components.registerAdapter(XMLInputCell, models.IInputCell, IXML)

#-------------------------------------------------------------------------------
# Notebook object from XML strings
#-------------------------------------------------------------------------------

def NotebookFromXML(session, s):
    """Return a notebook from an XML string"""
    f = StringIO.StringIO(s)
    tree = ET.ElementTree(file=f)
    nb = NotebookFromElement(session, tree.getroot())
    f.close()
    session.save(nb)
    session.flush()
    return nb

def NotebookFromElement(session, nbe):
    uname = nbe.find('username').text
    email = nbe.find('email').text
    try:
        user = session.query(models.User).selectone_by(username=uname)
    except:
        user  = dbutil.createUser(session, uname, email)
    dc = datetime.datetime.strptime(nbe.find('dateCreated').text, tformat)
    dm = datetime.datetime.strptime(nbe.find('dateModified').text, tformat)
    nb = models.Notebook()
    nb.user = user
    nb.dateCreated = dc
    nb.dateModified = dm
    nb.root = anyCellFromElement(session, nbe.find('MultiCell'))
    session.save(nb)
    session.flush()
    return nb

def anyCellFromElement(session, element):
    if element.tag == 'MultiCell':
        cell = multiCellFromElement(session, element)
    elif element.tag == 'TextCell':
        cell = textCellFromElement(element)
    elif element.tag == 'InputCell':
        cell = inputCellFromElement(element)
    session.save(cell)
    session.flush()
    return cell

def initCfromE(element):
    dc = datetime.datetime.strptime(element.find('dateCreated').text, tformat)
    dm = datetime.datetime.strptime(element.find('dateModified').text, tformat)
    comment = element.find('comment').text
    return (dc,dm,comment)

def textCellFromElement(element):
    cell = models.TextCell()
    cell.dateCreated, cell.dateModified, cell.comment = initCfromE(element)
    cell.textData = element.find('textData').text
    return cell

def inputCellFromElement(element):
    cell = models.InputCell()
    cell.dateCreated, cell.dateModified, cell.comment = initCfromE(element)
    cell.input = element.find('input').text
    cell.output = element.find('output').text
    return cell

def multiCellFromElement(session, element):
    cell = models.MultiCell()
    cell.dateCreated, cell.dateModified, cell.comment = initCfromE(element)
    cell.title = element.find('title').text
    kids = element.findall('MultiCell')+element.findall('InputCell')+\
                    element.findall('TextCell')
    for e in kids:
        c = anyCellFromElement(session, e)
        dbutil.addChild(session, c, cell)
    return cell
    





