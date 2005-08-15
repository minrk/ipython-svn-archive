"""Formatter object for DocBook notebook sheets.
"""

from itertools import izip
import copy
from cgi import escape

from notabene.formatter import Formatter

from lxml import etree as ET

from PyFontify import fontify

def dbify(text):
    marker = 0
    for tag, start, end, sublist in fontify(text):
        if marker < start:
            yield escape(text[marker:start])
        yield ("""<phrase role="py_%s">%s</phrase>""" % 
            (tag, escape(text[start:end])))
        marker = end
    if marker < len(text):
        yield escape(text[marker:])

def transform_text(text):
    """used by the different transforms in DBFormatter"""
    return escape(text.rstrip())

class DBFormatter(Formatter):

    @staticmethod
    def prompt_length(number):
        return len(str(number)) + 7

    def transform_input(self, elem, number):
        text = elem.text.strip()

        # color the Python code
        text = ''.join(dbify(text.strip()))
        logid = elem.xpath("../../@id")[0]
        PS1 = (('<anchor id="%s-In%s"/>'
                '<phrase role="ipy_in_prompt">In [</phrase>'
                '<phrase role="ipy_in_number">%s</phrase>'
                '<phrase role="ipy_in_prompt">]:</phrase> ') %
                    (logid, number, number))
        dots = '...: '.rjust(self.prompt_length(number))
        PS2 = '<phrase role="ipy_in_prompt2">%s</phrase> ' % dots
        lines = text.split('\n')
        prompts = [PS1] + [PS2]*(len(lines)-1)
        
        wholetext = '\n'.join(x+y for x,y in izip(prompts, lines))
        return wholetext

    def transform_output(self, elem, number):
        text = transform_text(elem.text)
        logid = elem.xpath("../../@id")[0]
        PS3 = (('<anchor id="%s-Out%s"/>'
                '<phrase role="ipy_out_prompt">Out[</phrase>'
                '<phrase role="ipy_out_number">%s</phrase>'
                '<phrase role="ipy_out_prompt">]:</phrase> ')
                    % (logid, number, number))

        lines = text.split('\n')
        first = PS3 + lines[0]
        if len(lines) > 1:
            last = self.indent('\n'.join(lines[1:]), self.prompt_length(number))
            wholetext = '%s\n%s' % (first, last)
        else:
            wholetext = first
        return wholetext

    def transform_stdout(self, elem, number):
        text = transform_text(elem.text)
        logid = elem.xpath("../../@id")[0]
        wholetext = ('<anchor id="%s-stdout%s"/>%s' % 
                        (logid, number, text))
        return wholetext

    def transform_stderr(self, elem, number):
        text = transform_text(elem.text)
        logid = elem.xpath("../../@id")[0]
        wholetext = ('<anchor id="%s-stderr%s"/>%s' % 
                        (logid, number, text))
        return wholetext

    def transform_traceback(self, elem, number):
        text = transform_text(elem.text)
        logid = elem.xpath("../../@id")[0]
        wholetext = ('<anchor id="%s-traceback%s"/>%s' % 
                        (logid, number, text))
        return wholetext

    def transform_figure(self, fig):
        #logid = elem.xpath("../../@id")[0]
        ET.dump(fig)
        number = fig.get('number')
        dbfig = ET.Element('figure', label="Fig%s"%(number))
        dbmedia = ET.SubElement(dbfig, "mediaobject")
        dbimage = ET.SubElement(dbmedia, "imageobject")
        dbimagedata = ET.SubElement(dbimage, "imagedata",
            fileref=fig.get('filename'))

        caption = fig.get('caption')
        if caption and caption.strip():
            captelem = ET.SubElement(dbimage, "caption")
            para = ET.SubElement(captelem, "para")
            strong = ET.SubElement(para, "phrase", role="ipy_fig_prompt")
            strong.text = 'Fig[%s]: ' % number
            strong.tail = caption.strip()
        dbfig.tail = fig.tail
        ET.dump(dbfig)
        return dbfig

    def transform_equation(self, equ):
        """This uses the old method that uses graphic for image. It is unfortunate because otherwise the graphic-element is not used for images anymore, but mediaobject imageobjects instead. Perhaps we should just fix db2latex to get this right?"""
        dbeq = ET.Element('equation')
        title = equ.get('title')
        tex = equ.get('tex')
        if title is not None:
            dbtit = ET.SubElement(dbeq, 'title')
            dbtit.text = title
        dbmath = ET.SubElement(dbeq, 'alt', role="tex")
        dbmath.text = tex
        #XXX add image support (for html & nbshell) here .. somewhere
        return dbeq

    def transform_block(self, block):
        """Transform an <ipython-block> element to a <programlisting> element.
        """

        logid = block.get('logid', 'default-log')
        texts = []
        for cell in block:
            number = cell.get('number')
            type = cell.get('type')
            try:
                elem = self.notebook.get_from_log(type, number, logid=logid)
            except ValueError: #XXX prob with nbshell products
                print number, "not in", self.notebook, "? - ignoring."
                continue
            
            if type in ('input', 'special-input'):
                texts.append(self.transform_input(elem, number))
            else:
                try:
                    xform = getattr(self, "transform_%s" % type)
                except AttributeError:
                    raise NotImplementedError
                texts.append(xform(elem, number))

        listing = ET.XML('<programlisting role="ipy_block">%s</programlisting>'
                    % '\n'.join(texts))

        # <ipython-block>'s might be in mixed-content, so preserve the tail text
        listing.tail = block.tail
        return listing

    def transform_sheet(self, sheet, nodetype='article'):
        """Transform a <sheet> element to a <section> element.
        """
        # Good G-d! Is this *really* the only way to copy an element(tree)?
        sheet2 = ET.XML(ET.tostring(sheet))
        # not with lxml!
        #sheet2 = copy.deepcopy(sheet)
        # or maybe it is

        # get all child->parent links
        cp = dict((c, p) for p in sheet2.getiterator() for c in p)

        def parent_and_index(elem):
            parent = cp[elem]
            index = list(parent).index(elem)
            return parent, index

        def transform_elements(elemtype, func):
            elems = sheet2.xpath('.//ipython-%s' % elemtype)
            for elem in elems:
                parent, idx = parent_and_index(elem)
                transformed = func(elem)
                parent[idx] = transformed

        transform_elements('block', self.transform_block)
        transform_elements('figure', self.transform_figure)

        ## figs = sheet2.xpath('.//ipython-figure')
##         for fig in figs:
##             parent, idx = parent_and_index(fig)
##             number = fig.get('number')
##             #logid = fig.get('logid', 'default-log')
##             #elem = self.notebook.get_from_log('figure', number, logid=logid)
##             img = self.transform_figure(fig)
##             parent[idx] = img

        transform_elements('equation', self.transform_equation)

        sheet2.tag = nodetype
        # get rid of 'type' attribute -- depracated
        try:
            del sheet2.attrib['type']
        except KeyError:
            print "sheet(2) had no type attr to delete."
                    
        return sheet2

    def format_sheet(self, sheet):
        """Format a <sheet> element to DocBook text.
        """
        newsheet = self.transform_sheet(sheet)
        return ET.tostring(newsheet)

    @staticmethod
    def escape_latex(text):
        if text is None:
            return None
        return text.replace('\\', r'\\').replace('{', r'\{').replace('}', r'\}')
    def prep_fo(self, tree):
        pass

    def prep_html(self, tree):
        pass

    def prep_latex(self, tree):
        listings = tree.xpath('//programlisting') 
        for listing in listings:  
            listing.text = self.escape_latex(listing.text)  
            for sub in listing.getiterator():  
                sub.text = self.escape_latex(sub.text)
                sub.tail = self.escape_latex(sub.tail)  

    def to_text(self, sheet, kind='html', style=None):
        if style is None:
            from notabene.styles import LightBGStyle as style
        xsl = getattr(style, '%s_xsl'%kind)()
        xslt = ET.XSLT(xsl)
        article_tree = ET.ElementTree(self.transform_sheet(sheet))
        getattr(self, 'prep_%s' % kind)(article_tree)
        newtree = xslt.apply(article_tree)
        return newtree
