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
        s += models.indent(u.xmlize(justme=flatten),2)
        if flatten:
            for node in session.query(models.Node).select():
                s += models.indent(node.xmlize(justme=True),2)
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

def initFromE(Klass, element):
    c = Klass()
    c.dateCreated = datetime.datetime.strptime(element.find('dateCreated').text, tformat)
    c.dateModified = datetime.datetime.strptime(element.find('dateModified').text, tformat)
    # c.userID = int(element.find('userID').text)
    return c
    
def userFromElement(session, ue):
    username = ue.find('username').text
    email = ue.find('email').text
    try: # get from db
        user = session.query(models.User).selectone_by(username=username, email=email)
    except: # user does not exist, so add to db
        user = initFromE(models.User, ue)
        user.username = username
        user.email = email
        session.save(user)
        session.flush()
    justme = bool(ue.find('justme').text)
    nodes = {}
    if not justme:
        for nbe in ue.find('Notebooks').findall('Section'):
            s = sectionFromElement(session, nbe, user, None, nodes)
    # session.flush()
    nodes[None] = models.Node()
    print nodes
    for node in nodes.values(): # correct node ID values
        node.nextID = nodes[node.nextID].nodeID
        node.previousID = nodes[node.previousID].nodeID
        if isinstance(node, models.Section):
            node.headID = nodes[node.headID].nodeID
            node.tailID = nodes[node.headID].nodeID
    session.flush()
    return user
        
    
def anyNodeFromElement(session, element, user, parent, nodes):
    """switcher function"""
    if element.tag == 'Section':
        cell = sectionFromElement(session, element, user, parent, nodes)
    elif element.tag == 'TextCell':
        cell = textCellFromElement(session, element, user, parent, nodes)
    elif element.tag == 'InputCell':
        cell = inputCellFromElement(session, element, user, parent, nodes)
    else:
        raise Exception("We have no way to handle: %s"%element.tag)
    return cell

def initNodeFromE(Klass, session, element, user, parent, nodes):
    node = initFromE(Klass, element)
    node.comment = element.find('comment').text
    session.save(node)
    session.flush()
    for idname in ['nextID', 'previousID']:
        s = element.find(idname).text
        if s:
            value = int(s)
        else:
            value = None
        setattr(node, idname, value)
    node.user = user
    node.parent = parent
    nodeID = int(element.find('nodeID').text)
    nodes[nodeID] = node
    print nodeID, nodes
    return node

def textCellFromElement(session, element, user, parent, nodes):
    cell = initNodeFromE(models.TextCell, session, element, user, parent, nodes)
    cell.textData = element.find('textData').text
    return cell

def inputCellFromElement(session, element, user, parent, nodes):
    cell = initNodeFromE(models.InputCell, session, element, user, parent, nodes)
    cell.input = element.find('input').text
    cell.output = element.find('output').text
    return cell

def sectionFromElement(session, element, user, parent, nodes):
    sec = initNodeFromE(models.Section, session, element, user, parent, nodes)
    sec.title = element.find('title').text
    kide = element.find('children')
    justme = bool(element.find('justme').text)
    if not justme:
        for e in kide.findall('Section')+kide.findall('InputCell')+\
                        kide.findall('TextCell'):
            print e.tag
            anyNodeFromElement(session, e, user, sec, nodes)
    return sec

def loadDBFromXML(session, s, isfilename=False, flatten=False):
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
        print obj
        session.save(obj)
    session.flush()

