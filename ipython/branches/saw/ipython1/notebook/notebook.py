# encoding: utf-8
# -*- test-case-name: ipython1.test.test_task -*-
"""The main notebook system
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

#-------------------------------------------------------------------------------
# Notebook interfaces
#-------------------------------------------------------------------------------

class INode(zi.Interface):
    """The Basic Node Interface"""
    
    children = zi.Attribute("Dict: the children of the node")
    parent = zi.Attribute("Node: The parent object of the node (default:None)")
    
    def addChild(child, index=None):
        """adds `child` to the node at `index`, defaulting to the end"""
    
    def popChild(index):
        """removes the child at `index`"""
    


class ICell(zi.Interface):
    """The Basic Cell Interface"""
    
    parent = zi.Attribute("Node: The parent object of the cell")
    dateCreated = zi.Attribute("String: The date the cell was created")
    dateModified = zi.Attribute("String: The date the cell was most recently modified")
    tags = zi.Attribute("Dict: Tags used for searching")


class ITextCell(ICell):
    """A Basic text cell"""
    
    text = zi.Attribute("String: the text of the cell")
    format = zi.Attribute("String: the formatting for the text")
    

class IIOCell(ICELL):
    """A Basic I/O Cell"""
    
    input = zi.Attribute("String: input python code")
    output = zi.Attribute("String: The output of input")

class IImageCell(ICELL):
    """A Basic Cell for images"""
    
    image = zi.Attribute("Image: The image object")

