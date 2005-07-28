"""Class Sheet. Responsible for storing and manipulating data in the <sheet> tag"""

#*****************************************************************************
#       Copyright (C) 2005 Tzanko Matev. <tsanko@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from nbshell import Release
__author__  = '%s <%s>' % Release.author
__license__ = Release.license
__version__ = Release.version


from lxml import etree

class Sheet(object):
    def __init__(self, doc, notebook):
        self.doc = doc
        self.notebook = notebook
        self.element = self.notebook.root.xpath('//sheet')[0]
