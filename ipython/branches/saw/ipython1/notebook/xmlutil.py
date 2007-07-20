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
import StringIO, datetime, os.path
try:
    import xml.etree.ElementTree as ET
except ImportError:
    import elementree.ElementTree as ET

from twisted.python import components

from ipython1.notebook import models, dbutil

tformat = models.tformat
#-------------------------------------------------------------------------------
# Export a Notebook to XML
#-------------------------------------------------------------------------------

def dumpDBtoXML(session, fname=None, flatten=False):
    """Build an XML String"""
    users = session.query(models.User).select()
    s = "<XMLBackup>\n"
    for u in users:
        s += models.indent(u.xmlize(),2)
        if flatten:
            for node in session.query(models.Node).select():
                s += models.indent(node.xmlize(justme=True),2)
        else:
            for nb in u.notebooks:
                s += models.indent(nb.xmlize(justme=False),4)
    s += "</XMLBackup>\n"
    
    if fname is not None:
        f = open(fname, 'w')
        f.write(s)
        f.close()
    else:
        return s

#-------------------------------------------------------------------------------
# Notebook object from XML strings
#-------------------------------------------------------------------------------

def initFromE(Klass,element):
    c = Klass()
    c.dateCreated = datetime.datetime.strptime(element.find('dateCreated').text, tformat)
    c.dateModified = datetime.datetime.strptime(element.find('dateModified').text, tformat)
    c.userID = int(element.find('userID').text)
    return c
    
def userFromElement(session, ue):
    user = initFromE(models.User, ue)
    user.username = ue.find('username').text
    user.email = ue.find('email').text
    
def anyNodeFromElement(element, flatten):
    """switcher function"""
    if element.tag == 'Section':
        cell = sectionFromElement(element, flatten)
    elif element.tag == 'TextCell':
        cell = textCellFromElement(element)
    elif element.tag == 'InputCell':
        cell = inputCellFromElement(element)
    return cell

def initNodeFromE(Klass, element):
    node = initFromE(Klass, element)
    node.comment = element.find('comment').text
    for idname in ['nodeID', 'parentID', 'nextID', 'previousID', 'userID']:
        s = element.find(idname).text
        if s:
            value = int(s)
        else:
            value = None
        setattr(node, idname, value)
    return node

def textCellFromElement(element):
    cell = initNodeFromE(models.TextCell, element)
    cell.textData = element.find('textData').text
    return cell

def inputCellFromElement(element):
    cell = initNodeFromE(models.InputCell, element)
    cell.input = element.find('input').text
    cell.output = element.find('output').text
    return cell

def sectionFromElement(element, flatten):
    sec = initNodeFromE(models.Section, element)
    sec.title = element.find('title').text
    kide = element.find('children')
    if not flatten:
        for e in kide.findall('Section')+element.findall('InputCell')+\
                        element.findall('TextCell'):
            anyNodeFromElement(e, flatten)
    return sec

def loadDBFromXML(session, s=None, isfilename=False, flatten=False):
    """Return a notebook from an XML string or file"""
    if isfilename:
        f = open(s)
    else:
        f = StringIO.StringIO(s)
    tree = ET.ElementTree(file=f)
    root = tree.getroot()
    userElements = root.findall('User')
    sectionElements = root.findall('Section')
    cellElements = root.findall('InputCell')+root.findall('TextCell')
    if cellElements:
        # override the flatten setting if non-Sections are in the base
        flatten = True
    users = [userFromElement(session, ue) for ue in userElements]
    sections = [sectionFromElement(session, se, flatten) for se in sectionElements]
    cells = [anyNodeFromElement(session, cell, flatten) for cell in cellElements]
    
    f.close()
    for obj in users+sections+cells:
        session.save(obj)
    session.flush()

