# Author: Robert Kern
# Contact: rkern@ucsd.edu
# Date: 2005-07-07
# Copyright: Copyright 2005 by Robert Kern. 
#   All rights reserved.
#   This software is provided without warranty under the terms of the BSD
#   license. http://opensource.org/licenses/bsd-license.php

from docutils import nodes, utils

try:
    from lxml import etree as ET
except ImportError:
    try:
        import cElementTree as ET
    except ImportError:
        from elementtree import ElementTree as ET

class XMLReader(object):
    """Convert the XML representation of a Docutils document back to the
    internal representation.

    :Constructors:
        XMLReader(tree) -- tree is an ElementTree
        XMLReader.fromfile(source) -- source is a filename or file-like object
        XMLReader.fromstring(source) -- source is a string of XML data
    """
    def __init__(self, tree):
        self.tree = tree

    @classmethod
    def fromfile(cls, source):
        tree = ET.parse(source)
        return cls(tree)

    @classmethod
    def fromstring(cls, source):
        tree = ET.fromstring(source)
        return cls(tree)

    def convert_element(self, elem):
        """Recursively convert an element from the ElementTree to Docutils
        Nodes.
        """
        if elem.tag == 'document':
            node = utils.new_document('*XML*')
        else:
            nodetype = getattr(nodes, elem.tag)
            node = nodetype()
        for attr in elem.keys():
            if attr != '{http://www.w3.org/XML/1998/namespace}space':
                # this is just part of the XML output, not the docutil node
                node[attr] = elem.get(attr)
        if elem.text:
            node.append(nodes.Text(elem.text))
        for child in elem:
            node.append(self.convert_element(child))
            if child.tail:
                node.append(nodes.Text(child.tail))
        return node
                    
    def as_document(self):
        """Convert the whole tree in self.tree to a Docutils doctree.
        """
        root = self.tree.getroot()
        return self.convert_element(root)

