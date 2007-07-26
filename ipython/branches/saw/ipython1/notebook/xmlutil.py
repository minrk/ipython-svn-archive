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
def unxmlsafe(s):
    if s is None:
        return None
    return s.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&amp;", "&")

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
    
def userFromElement(session, ue, nodes={}):
    username = unxmlsafe(ue.find('username').text)
    email = unxmlsafe(ue.find('email').text)
    try: # get from db
        user = session.query(models.User).selectone_by(username=username, email=email)
    except: # user does not exist, so add to db
        user = initFromE(models.User, ue)
        user.username = username
        user.email = email
        session.save(user)
        session.flush()
    justme = bool(ue.find('justme').text)
    if not justme:
        for nbe in ue.find('Notebooks').findall('Section'):
            s = sectionFromElement(nbe, user, None, nodes)
    return user
        
    
def anyNodeFromElement(element, user, parent, nodes={}):
    """switcher function"""
    if element.tag == 'Section':
        cell = sectionFromElement(element, user, parent, nodes)
    elif element.tag == 'TextCell':
        cell = textCellFromElement(element, user, parent, nodes)
    elif element.tag == 'InputCell':
        cell = inputCellFromElement(element, user, parent, nodes)
    else:
        raise Exception("We have no way to handle: %s"%element.tag)
    return cell

def initNodeFromE(Klass, element, user, parent, nodes):
    node = initFromE(Klass, element)
    node.comment = unxmlsafe(element.find('comment').text)
    # session.save(node)
    # session.flush()
    for idname in ['nextID', 'previousID', 'parentID']:
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
    # check for existing node, if updating
    # print nodeID, nodes
    return node

def textCellFromElement(element, user, parent, nodes):
    cell = initNodeFromE(models.TextCell, element, user, parent, nodes)
    cell.textData = unxmlsafe(element.find('textData').text)
    return cell

def inputCellFromElement(element, user, parent, nodes):
    cell = initNodeFromE(models.InputCell, element, user, parent, nodes)
    cell.input = unxmlsafe(element.find('input').text)
    cell.output = unxmlsafe(element.find('output').text)
    return cell

def sectionFromElement(element, user, parent, nodes):
    sec = initNodeFromE(models.Section, element, user, parent, nodes)
    sec.title = unxmlsafe(element.find('title').text)
    for idname in ['headID', 'tailID']:
        s = element.find(idname).text
        if s:
            value = int(s)
        else:
            value = None
        setattr(sec, idname, value)
    kide = element.find('children')
    justme = bool(element.find('justme').text)
    if not justme:
        for e in kide.findall('Section')+kide.findall('InputCell')+\
                        kide.findall('TextCell'):
            # print e.tag
            anyNodeFromElement(e, user, sec, nodes)
    return sec

def saveAndRelink(session, nodes):
    for node in nodes.values():
        session.save(node)
    session.flush()
    # nodes[None] = models.Node()
    for node in nodes.values(): # correct node ID values
        for key in ['next', 'previous', 'parent']:
            try:
                id = nodes.get(getattr(node, key+"ID")).nodeID
            except AttributeError:
                id = None
            setattr(node, key+"ID", id)
        # node.nextID = nodes[node.nextID].nodeID
        # node.previousID = nodes[node.previousID].nodeID
        if isinstance(node, models.Section):
            # print "SECTION"
            for key in ['head', 'tail']:
                try:
                    id = nodes.get(getattr(node, key+"ID")).nodeID
                except AttributeError:
                    id = None
                setattr(node, key+"ID", id)
            # node.headID = nodes[node.headID].nodeID
            # node.tailID = nodes[node.headID].nodeID
    session.flush()
    for node in nodes.values():
        session.refresh(node)
    return nodes

def loadDBFromXML(session, s, isfilename=False, flatten=False):
    """loads a whole DB Backup from an XML string or file"""
    if isfilename:
        f = open(s)
    else:
        f = StringIO.StringIO(s)
    tree = ET.ElementTree(file=f)
    root = tree.getroot()
    userElements = root.findall('User')
    nodeElements = root.findall('Section')+root.findall('InputCell')+root.findall('TextCell')
    if nodeElements:
        # override the flatten setting if non-Sections are in the base
        flatten = True
    if flatten:
        raise NotImplementedError
    
    nodes = {}
    users = [userFromElement(session, ue, nodes) for ue in userElements]
    # nodelist = [anyNodeFromElement(e, user, parent, nodes) for e in nodeElements]
    
    f.close()
    
    saveAndRelink(session, nodes)

def loadNotebookFromXML(session, s, user, isfilename=False, flatten=False):
    if isfilename:
        f = open(s)
    else:
        f = StringIO.StringIO(s)
    tree = ET.ElementTree(file=f)
    root = tree.getroot()
    nodes = {}
    sec = sectionFromElement(root, user, None, nodes)
    f.close()
    saveAndRelink(session, nodes)
    session.refresh(user)
    return sec

