"""Formatter object for DocBook notebook sheets.
"""

from itertools import izip
import copy
from cgi import escape

from nb_formatter import Formatter

from lxml import etree as ET

from PyFontify import fontify

def dbify(text):
    marker = 0
    for tag, start, end, sublist in fontify(text):
        if marker < start:
            yield escape(text[marker:start])
        yield ("""<db:phrase role="py_%s">%s</db:phrase>""" % 
            (tag, escape(text[start:end])))
        marker = end
    if marker < len(text):
        yield escape(text[marker:])

class DBSectionFormatter(Formatter):

    @staticmethod
    def prompt_length(number):
        return len(str(number)) + 7

    def transform_input(self, elem):
        text = elem.text.strip()

        # color the Python code
        text = ''.join(dbify(text.strip()))
        number = elem.get('number')
        logid = elem.xpath("../@id")[0]
        PS1 = (('<db:anchor xml:id="%s-In%s">'
                '<db:phrase role="ipy_in_prompt">In [</db:phrase>'
                '<db:phrase role="ipy_in_number">%s</db:phrase>'
                '<db:phrase role="ipy_in_prompt">]:</db:phrase></db:anchor> ') %
                    (logid, number, number))
        dots = '...: '.rjust(self.prompt_length(number))
        PS2 = '<db:phrase role="ipy_in_prompt2">%s</db:phrase> ' % dots
        lines = text.split('\n')
        prompts = [PS1] + [PS2]*(len(lines)-1)
        
        wholetext = '\n'.join(x+y for x,y in izip(prompts, lines))
        return wholetext

    def transform_output(self, elem):
        text = elem.text.strip()
        number = elem.get('number')
        logid = elem.xpath("../@id")[0]
        PS3 = (('<db:anchor xml:id="%s-Out%s">'
                '<db:phrase role="ipy_out_prompt">Out[</db:phrase>'
                '<db:phrase role="ipy_out_number">%s</db:phrase>'
                '<db:phrase role="ipy_out_prompt">]:</db:phrase>'
                '</db:anchor> ') 
                    % (logid, number, number))

        lines = text.split('\n')
        first = PS3 + lines[0]
        last = self.indent('\n'.join(lines[1:]), self.prompt_length())

        wholetext = '%s\n%s' % (first, last)
        return wholetext

    def transform_stdout(self, elem):
        text = elem.text.strip()
        number = elem.get('number')
        logid = elem.xpath("../@id")[0]
        text = self.indent(text, self.prompt_length(number))
        wholetext = ('<db:anchor xml:id="%s-stdout%s">%s</db:anchor>' % 
                        (logid, number, text))
        return wholetext

    def transform_stderr(self, elem):
        text = elem.text.strip()
        number = elem.get('number')
        logid = elem.xpath("../@id")[0]
        text = self.indent(text, self.prompt_length(number))
        wholetext = ('<db:anchor xml:id="%s-stderr%s">%s</db:anchor>' % 
                        (logid, number, text))
        return wholetext

    def transform_traceback(self, elem):
        text = elem.text.strip()
        number = elem.get('number')
        logid = elem.xpath("../@id")[0]
        text = self.indent(text, self.prompt_length(number))
        wholetext = ('<db:anchor xml:id="%s-traceback%s">%s</db:anchor>' % 
                        (logid, number, text))
        return wholetext

    def transform_figure(self, elem):
        logid = elem.xpath("../@id")[0]
        number = elem.get('number')
        dbfig = ET.Element('db:figure', label="%s-Fig%s"%(logid,number))
        dbmedia = ET.SubElement(dbfig, "db:mediaobject")
        dbimage = ET.SubElement(dbmedia, "db:imageobject",
            fileref=elem.get('filename'))

        caption = elem.text
        if caption and caption.strip():
            captelem = ET.SubElement(dbimage, "db:caption")
            para = ET.SubElement(captelem, "db:para")
            strong = ET.SubElement(para, "db:phrase", role="ipy_fig_prompt")
            strong.text = 'Fig[%s]: ' % number
            strong.tail = caption.strip()
        dbfig.tail = elem.tail
        return dbfig

    def transform_block(self, block):
        """Transform an <ipython-block> element to a <programlisting> element.
        """

        logid = block.get('logid', 'default-log')
        texts = []
        for cell in block:
            number = cell.get('number')
            type = cell.get('type')
            elem = self.notebook.get_from_log(type, number, logid=logid)
            if type in ('input', 'special-input'):
                texts.append(self.transform_input(elem))
            else:
                try:
                    xform = getattr(self, "transform_%s" % type)
                except AttributeError:
                    raise NotImplementedError
                texts.append(xform(elem))

        listing = ('<db:programlisting role="ipy_block">%s</db:programlisting>'
                    % '\n'.join(texts))

        # <ipython-block>'s might be in mixed-content, so preserve the tail text
        listing.tail = block.tail
        return listing

    def transform_sheet(self, sheet):
        """Transform a <sheet> element to a <section> element.
        """
        # Good G-d! Is this *really* the only way to copy an element(tree)?
        #sheet2 = ET.XML(ET.tostring(sheet))
        # not with lxml!
        sheet2 = copy.deepcopy(sheet)

        # get all child->parent links
        cp = dict((c, p) for p in sheet2.getiterator() for c in p)

        blocks = sheet2.findall('ipython-block')
        for block in blocks:
            parent = cp[block]
            idx = list(parent).index(block)
            listing = self.transform_block(block)
            parent[idx] = listing

        figs = sheet2.findall('ipython-figure')
        for fig in figs:
            parent = cp[fig]
            idx = list(parent).index(fig)
            number = fig.get('number')
            logid = fig.get('logid', 'default-log')
            elem = self.notebook.get_from_log('figure', number, logid=logid)
            img = self.transform_figure(elem)
            parent[idx] = img

        sheet2.tag = 'section'
        # get rid of 'type' attribute
        sheet2.attrib.pop('type')
        return sheet2

    def format_sheet(self, sheet):
        """Format a <sheet> element to DocBook text.
        """
        newsheet = self.transform_sheet(sheet)
        return ET.tostring(newsheet)

class DBFormatter(DBSectionFormatter):

    def get_template(self):
        html = ET.Element('article')
        return html

    def transform_sheet(self, sheet):
        """Transform a <sheet> to a full <article> elemnt.
        """
        template = self.get_template()
        section = super(self.__class__, self).transform_sheet(sheet)
        template.append(section)
        return template


