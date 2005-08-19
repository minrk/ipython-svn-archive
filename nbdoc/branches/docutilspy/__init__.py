"""The notebook public interface for friendly writing of notebooks.

This now uses the docutils backend, but might also use perhaps ElementTree or also LaTEX directly -- those issues are under study.

Perhaps the next thing to tackle is graphs, probably first with the existing gnuplot wrappings."""

from docutils import nodes

def new_document():
    """There is a similar utility in docutils.utils but it supposes a file source (right?), and does not work straight for (at least) html output (?)"""

    from docutils import frontend #these are only needed here
    from docutils.utils import Reporter

    source = None
    settings = frontend.OptionParser().get_default_values()

    #these needed for getting a html out - where are the defaults?
    settings.xml_declaration = False
    settings.embed_stylesheet = False
    settings.stylesheet_path = False
    settings.stylesheet = None
    settings.initial_header_level = "1"

    #an attempt to make docutils.nodes.NodeVisitor accept notebook classes
    

    #this is one-to-one from docutils.utils new_document
    reporter = Reporter(source, settings.report_level, settings.halt_level,
                        stream=settings.warning_stream, debug=settings.debug,
                        encoding=settings.error_encoding,
                        error_handler=settings.error_encoding_error_handler)

    document = nodes.document(settings, reporter)
    return document

document = new_document() #singleton to which elements are automagically added

def write():
    """A simple command to get the notebook document. Now defaults to HTML."""

    import docutils, docutils.io
    from docutils.writers.html4css1 import Writer

    out = docutils.io.FileOutput()
    out.encoding = 'unicode'
    w = Writer()
    w.write(document, out)

class Element(nodes.Element):
    """An abstract baseclass for all notebook elements (parts).

    This implementation extends directly the docutils Element"""

    def __init__(self):
        """Automagically adds itself to the document singleton at creation.

        The implementing classes are to always use self.document,
        this being the only place where the singleton/global
        getting is specified."""
        
        self.document = document
        self.document += self

class TextElement(Element, nodes.TextElement):
    """An abstract baseclass for all elements that have text."""

    def __init__(self, text):
        print "---", text
        nodes.TextElement.__init__(self, text=text)
        Element.__init__(self)

class section(nodes.section, Element): #does not have .children if vice-versa
    def __init__(self):
        nodes.section.__init__(self)
        Element.__init__(self)
# __name__ = 'section' #for docutils.nodes.NodeVisitor dispatch
Section = section #oh well :)

class title(TextElement, nodes.title): pass
Title = title

class subtitle(TextElement, nodes.subtitle): pass
Subtitle = subtitle

class paragraph(TextElement, nodes.paragraph): pass
Paragraph = paragraph

if __name__ == '__main__':
    sect = Section()
    print document
