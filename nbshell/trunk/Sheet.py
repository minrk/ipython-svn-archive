"""Class Sheet. Responsible for storing and manipulating data in the <sheet> tag"""
from lxml import etree

class Sheet(object):
    def __init__(self, doc, notebook):
        self.doc = doc
        self.notebook = notebook
        self.element = self.notebook.root.xpath('//sheet')[0]
