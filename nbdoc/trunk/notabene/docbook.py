"""Formatter object for DocBook notebook sheets.
"""

from itertools import izip
import copy
from cgi import escape
import os
import tempfile
import subprocess

from lxml import etree as ET

from notabene.formatter import Formatter
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
        return dbfig

    def transform_equation(self, equ):
        # This uses the old method that uses graphic for image. It is
        # unfortunate because otherwise the graphic-element is not used for images
        # anymore, but mediaobject imageobjects instead. Perhaps we should just
        # fix db2latex to get this right?
        dbeq = ET.Element('informalequation')
        tex = equ.text
        verbatim = equ.get('verb', None)
        if verbatim != '1':
            tex = r'\begin{equation}%s\end{equation}' % tex
        mo = ET.SubElement(dbeq, 'mediaobject')
        to = ET.SubElement(mo, 'textobject')
        phrase = ET.SubElement(to, 'phrase', role="latex")
        phrase.text = tex
        # XXX: add image support (for html & nbshell) here .. somewhere
        dbeq.tail = equ.tail
        return dbeq

    def transform_inlineequation(self, equ):
        dbeq = ET.Element('inlineequation')
        tex = equ.text
        verbatim = equ.get('verb', None)
        if verbatim != '1':
            tex = r'$%s$' % tex
        mo = ET.SubElement(dbeq, 'inlinemediaobject')
        to = ET.SubElement(mo, 'textobject')
        phrase = ET.SubElement(to, 'phrase', role="latex")
        phrase.text = tex
        # XXX: add image support (for html & nbshell) here .. somewhere
        dbeq.tail = equ.tail
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
        transform_elements('equation', self.transform_equation)
        transform_elements('inlineequation', self.transform_inlineequation)

        sheet2.tag = nodetype
        return sheet2

    def format_sheet(self, sheet):
        """Format a <sheet> element to DocBook text.
        """
        newsheet = self.transform_sheet(sheet)
        return ET.tostring(newsheet, encoding='utf8')

    @staticmethod
    def escape_latex(text):
        if text is None:
            return None
        return text.replace('\\', r'\\').replace('{', r'\{').replace('}', r'\}')
        
    @classmethod
    def prep_fo(cls, tree):
        pass

    @classmethod
    def prep_html(cls, tree):
        pass
    
    @classmethod
    def prep_latex(cls, tree):
        listings = tree.xpath('//programlisting') 
        for listing in listings:  
            listing.text = cls.escape_latex(listing.text)  
            for sub in listing.getiterator():  
                sub.text = cls.escape_latex(sub.text)
                sub.tail = cls.escape_latex(sub.tail)  

    @classmethod
    def to_formatted(cls, dbxml, kind='html', style=None):
        """Convert a DocBook document to the final format.

        Returns a string containing the new document.
        """
        if style is None:
            from notabene.styles import LightBGStyle as style
        xsl = getattr(style, '%s_xsl'%kind)()
        xslt = ET.XSLT(xsl)
        if ET.iselement(dbxml):
            dbxml = ET.ElementTree(dbxml)
        getattr(cls, 'prep_%s' % kind)(dbxml)
        newtree = xslt.apply(dbxml)
        return xslt.tostring(newtree)

    @classmethod
    def write_formatted(cls, dbxml, name, format='html'):
        """Convert DocBook document to the format and write it to disk.
        
        This method will also run any post-processing necessary (e.g. pdflatex 
        to get PDF from LaTeX).
        
        Return the filename that was created.
        """
        extensions = {'latex': '.tex',
                      'html': '.html',
                      'doshtml': '.htm', #to allow specifying it explicitly
                      'pdf': '.pdf',
                      }

        base, ext = os.path.splitext(name) #allows giving also ext in name
        if ext not in extensions.values():
            #probably the name has a dot in it, like 'tut-2.3.5-db'
            base = name
            ext = False

        if not ext:
            ext = extensions.get(format, '.'+format)

        filename = os.path.abspath(base + ext)
        #could check if the given extension makes sense for the format

        toPDF = False
        if format == 'pdf':
            format = 'latex' #we get pdf via latex for now
            toPDF = True
            
        doc = cls.to_formatted(dbxml, kind=format).encode('utf-8')

        if toPDF:
            env = os.environ.copy()
            tmpfid, tmpfn = tempfile.mkstemp(suffix='.tex')
            tmpf = os.fdopen(tmpfid, 'w+b')
            try:
                tmpf.write(doc)
            finally:
                tmpf.close()
            try:
                # Try as hard as we can to output the PDF in the same directory
                # as the notebook file.
                dir, fn = os.path.split(filename)
                base = os.path.splitext(fn)[0]

                # Abusing TEXMFOUTPUT like this is a hideous hack that we need
                # to use for compatibility with teTeX < 3.0 and other older TeX
                # distributions. pdflatex only recently grew a nice
                # -output-directory option. This current strategy might be
                # unreliable; TEXMFOUTPUT only kicks in when "the current
                # directory is unwritable." We try to force that condition by
                # giving the full pathname as the jobname. That works on OS X at
                # least.
                env['TEXMFOUTPUT'] = dir

                #args = ['pdflatex', '-output-directory=%s'%dir, '-jobname=%s'%base]
                args = ['pdflatex', '-jobname=%s'%os.path.join(dir,base)]
                p = subprocess.Popen(args+[tmpfn], env=env)
                p.wait()
                # Do it a second time to make sure the references are right.
                p = subprocess.Popen(args+[tmpfn], env=env)
                p.wait()
            finally:
                os.unlink(tmpfn)

            return filename

        else:
            f = open(filename, 'wb')
            f.write(doc)
            f.close()
            return filename
    