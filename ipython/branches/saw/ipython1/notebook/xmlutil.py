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

from twisted.python import components

from ipython1.notebook import models


#-------------------------------------------------------------------------------
# XML representations of notebooks
#-------------------------------------------------------------------------------
def indent(s, n):
    """indent a multi-line string `s`, `n` spaces"""
    return " "*n+s.replace("\n", "\n"+" "*n)

class IXML(zi.Interface):
    """The class for adapting object to an XML string"""
    pass

def XMLNotebook(nb):
    """Return an XML representation of a notebook"""
    s  = "<dateCreated>%s</dateCreated>\n"%(nb.dateCreated)
    s += "<dateModified>%s</dateModified>\n"%(nb.dateModified)
    s += "<username>%s</username>\n"%(nb.user.username)
    s += "<email>%s</email>\n"%(nb.user.email)
    s += indent(IXML(nb.root), 2)
    return "<Notebook>\n"+indent(s,2)+"</Notebook>\n"
    s

def XMLNode(node):
    """Return an XML representation of a node"""
    s = "<title>%s</title>\n"%(node.title)
    for n in node.childrenNodes:
        s += indent(IXML(n), 2)
    for c in node.childrenCells:
        s += indent(IXML(c), 2)
    return "<Node>\n"+indent(s,2)+"</Node>\n"

def XMLTextCell(cell):
    s  = "<comment>%s</comment>\n"%(cell.comment)
    s += "<dateCreated>%s</dateCreated>\n"%(cell.dateCreated)
    s += "<dateModified>%s</dateModified>\n"%(cell.dateModified)
    s += "<textData>%s</textData>\n"%(cell.textData)
    return "<TextCell>\n"+indent(s,2)+"</TextCell>\n"

def XMLInputCell(cell):
    s  = "<comment>%s</comment>\n"%(cell.comment)
    s += "<dateCreated>%s</dateCreated>\n"%(cell.dateCreated)
    s += "<dateModified>%s</dateModified>\n"%(cell.dateModified)
    s += "<input>%s</input>\n"%(cell.input)
    s += "<output>%s</output>\n"%(cell.output)
    return "<InputCell>\n"+indent(s,2)+"</InputCell>\n"
    


components.registerAdapter(XMLNotebook, models.INotebook, IXML)
components.registerAdapter(XMLNode, models.INode, IXML)
components.registerAdapter(XMLTextCell, models.ITextCell, IXML)
components.registerAdapter(XMLInputCell, models.IInputCell, IXML)

#-------------------------------------------------------------------------------
# Notebook object from XML strings
#-------------------------------------------------------------------------------

