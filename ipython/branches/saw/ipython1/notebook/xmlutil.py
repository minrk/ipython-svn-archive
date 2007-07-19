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
import StringIO, datetime
try:
    import xml.etree.ElementTree as ET
except ImportError:
    import elementree.ElementTree as ET

from twisted.python import components

from ipython1.notebook import models, dbutil

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
    nb.root = anyNodeFromElement(session, nbe.find('Section'))
    session.save(nb)
    session.flush()
    return nb

def anyNodeFromElement(session, element):
    if element.tag == 'Section':
        cell = multiCellFromElement(session, element)
    elif element.tag == 'TextCell':
        cell = textCellFromElement(element)
    elif element.tag == 'InputCell':
        cell = inputCellFromElement(element)
    session.save(cell)
    session.flush()
    return cell

def initFromE(Klass, element):
    node = Klass()
    node.dateCreated = datetime.datetime.strptime(element.find('dateCreated').text, tformat)
    node.dateModified = datetime.datetime.strptime(element.find('dateModified').text, tformat)
    node.comment = element.find('comment').text
    return node

def textCellFromElement(element):
    cell = initFromE(models.TextCell, element)
    cell.textData = element.find('textData').text
    return cell

def inputCellFromElement(element):
    cell = initFromE(models.InputCell, element)
    cell.input = element.find('input').text
    cell.output = element.find('output').text
    return cell

def SectionFromElement(session, element):
    sec = initFromE(models.Section, element)
    sec.title = element.find('title').text
    kids = element.findall('Section')+element.findall('InputCell')+\
                    element.findall('TextCell')
    for e in kids:
        c = anyNodeFromElement(session, e)
        dbutil.addChild(session, c, sec)
    return sec



