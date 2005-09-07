from lxml import etree as ET
from notabene.notebook import Notebook

notebook = Notebook('None')

class StructureElement(object): #i.e. SheetElement?
    """All default to the same global Notebook, as this interface
    is for defining notebooks in Python, now one / process.."""
    def __init__(self):
        self.parent = notebook
        self.sheet = self.parent.sheet
        if self.sheet is None:
            self.parent.default_sheet()
            self.sheet = self.parent.sheet
            if self.sheet is None:
                #dbg
                #print "parent got no sheet after .default_sheet?"
                self.sheet = self.parent.default_sheet()
                self.parent.root.append(self.sheet)

class DocbookElement(object):
    def __init__(self, parent):
        #print "docbook element sheet", self.sheet
        pass
        #print "parent", parent, ET.tostring(parent.root)

class NamedElement(object):
    def __init__(self, name):
        self.name = self.element.attrib['name'] = name

class TextElement(object):
    def __init__(self, text): #python objects automatically have id
        #print "text: ", self, text
        self.text = self.element.text = text #is a sheet
    #def get_text(self):
    #    return self.element.text
    #text = property(get_gext)
        
class Title(TextElement, DocbookElement, StructureElement):
    name = 'title'
    def __init__(self, text):
        StructureElement.__init__(self) #sets parent and sheet
        DocbookElement.__init__(self, self.parent)
        if self.sheet is None:
            self.sheet = parent.default_sheet()
        self.element = ET.SubElement(self.sheet, self.name)
        TextElement.__init__(self, text)
       
class Subtitle(Title):
    name = 'subtitle'

class Paragraph(TextElement, DocbookElement):
    def __init__(self, text=None):
        self.element = ET.Element('paragraph')
        TextElement.__init__(self, text)
        
class Section(NamedElement, DocbookElement, StructureElement):
    def __init__(self, name):
        StructureElement.__init__(self)
        self.element = ET.SubElement(self.parent.sheet, 'section')
        NamedElement.__init__(self, name)
        #self.elements = []
        #dbg
        #print ET.tostring(self.element)

    def __add__(self, item):
        #self.elements.extend([item])
        self.element.append(item.element)
        

