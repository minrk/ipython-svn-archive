"""Formatter object for HTML notebook sheets.
"""

from nb_formatter import Formatter

try:
    import cElementTree as ET
except ImportError:
    from elementtree import ElementTree as ET

import PyHtmlify

CSS = """
body {
    background-color: #FFFFFF;
    color: #000;
    font-family: Verdana;
    font-size: 12px;
    line-height: 20px;
}

tt,pre {
    font-family: Lucida Console,Courier New,Courier,monotype;
    font-size: 100%
}

pre.code {
    background-color: #EEE;
    white-space:pre;
    color:#111111;
    padding: 0 0 0 0;
    width:100%;
    font-size: 10pt;
}

div.ipy_block {
    background-color: #EEE;
    display: table;
    margin-left: 10pt;
    padding-left: 1em;
    padding-right: 1em;
}
div.ipy_in_prompt {
    background-color: #EEE;
    max-width: 10em;
    display: table-cell;
}
div.ipy_out_prompt {
    background-color: #EEE;
    max-width: 10em;
    display: table-cell;
}
div.ipy_code {
    background-color: #EEE;
    display: table-cell;
}
div.ipy_input_bundle {
    background-color: #EEE;
    display: table-row;
    margin: 0;
    padding: 0;
}
div.ipy_output {
    background-color: #EEE;
    display: table-cell;
}
div.ipy_output_bundle {
    background-color: #EEE;
    display: table-row;
    margin: 0;
    padding: 0;
}

span.py_keyword     {color: #C00000;}
span.py_string      {color: #004080;}
span.py_comment     {color: #008000;}
span.py_identifier  {color: #0000C0;}

span.ipy_in_prompt {
    color: #00F;
    font-weight: bold;
}
span.ipy_in_number {
    color: #33F;
    font-weight: bold;
}
span.ipy_in_prompt2 {
    color: #00F;
    font-weight: bold;
}
span.ipy_out_prompt {
    color: #F00;
    font-weight: bold;
}
span.ipy_out_number {
    color: #F33;
    font-weight: bold;
}
"""


class HTMLFragmentFormatter(Formatter):
    """Formatter for HTML sheets to an HTML fragment.
    """

    # XXX: really should find a better place to put this.
    #    - Also, we should separate structural CSS from color/font styling; that's
    #      usually what the user is going to want to change.
    #    - And we should provide for file based CSS, too.
    CSS = CSS

    def transform_input(self, elem):
        """Transform a <[special-]input> element to a <div> element
        with syntax-colored content.
        """
        text = elem.text.strip()

        # color the Python code
        text = ''.join(PyHtmlify.htmlify(text.strip()))
        number = elem.attrib['number']
        PS1 = ('<a name="In%s"><span class="ipy_in_prompt">In [</span>'
               '<span class="ipy_in_number">%s</span>'
               '<span class="ipy_in_prompt">]:</span></a> ') % (number, number)
        dots = '...:'.rjust(len(number)+6)
        PS2 = '<span class="ipy_in_prompt2">%s</span> ' % dots
        lines = text.split('\n')
        prompts = [PS1] + [PS2]*(len(lines)-1)
        prompts_box = ET.XML('<pre class="code">%s</pre>' % '\n'.join(prompts))
        prompts_div = ET.Element('div')
        prompts_div.set('class', 'ipy_in_prompt')
        prompts_div.append(prompts_box)

        code_box = ET.XML('<pre class="code">%s</pre>' % text)
        code_div = ET.Element('div')
        code_div.set('class', 'ipy_code')
        code_div.append(code_box)

        whole_div = ET.Element('div')
        whole_div.set('class', 'ipy_input_bundle')
        whole_div.append(prompts_div)
        whole_div.append(code_div)

        return whole_div

    def transform_output(self, elem):
        """Transform an <output> element to a <div> element.
        """
        text = elem.text.strip()
        number = elem.attrib['number']
        PS3 = ('<a name="Out%s"><span class="ipy_out_prompt">Out[</span>'
               '<span class="ipy_out_number">%s</span>'
               '<span class="ipy_out_prompt">]:</span></a> ') % (number, number)
        prompts_box = ET.XML('<pre class="code">%s</pre>' % PS3)
        prompts_div = ET.Element('div')
        prompts_div.set('class', 'ipy_out_prompt')
        prompts_div.append(prompts_box)

        object_box = ET.XML('<pre class="code">%s</pre>' % text)
        object_div = ET.Element('div')
        object_div.set('class', 'ipy_output')
        object_div.append(object_box)

        whole_div = ET.Element('div')
        whole_div.set('class', 'ipy_output_bundle')
        whole_div.append(prompts_div)
        whole_div.append(object_div)

        return whole_div

    def transform_figure(self, elem):
        """Transform a <figure> element to an <img> element.
        """
        img = ET.Element('img')
        img.set('src', elem.get('filename'))

        # pass in appropriate attributes unchanged
        d = elem.attrib.copy()
        d.pop('filename', None)
        d.pop('type', None)
        number = d.pop('number')
        logid = d.pop('logid', 'default-log')
        img.attrib.update(d)

        caption = elem.text
        if caption and caption.strip():
            div = ET.Element('div')
            div.append(img)
            text = ET.SubElement(div, 'p')
            strong = ET.SubElement(text, 'strong')
            strong.text = 'Fig[%s]: ' % number
            strong.tail = caption.strip()
            new_elem = div
        else:
            new_elem = img
        new_elem.tail = elem.tail
        return new_elem

    def transform_block(self, block):
        """Transform an <ipython-block> element to a <div> element.
        """
        div = ET.Element('div')
        div.set('class', 'ipy_block')

        logid = block.get('logid', 'default-log')
        for cell in block:
            number = cell.get('number')
            type = cell.get('type')
            elem = self.notebook.get_from_log(type, number, logid=logid)
            if type in ('input', 'special-input'):
                div.append(self.transform_input(elem))
            elif type in ('output',):
                div.append(self.transform_output(elem))
            else:
                raise NotImplementedError

        # <ipython-block>'s might be in mixed-content, so preserve the tail text
        div.tail = block.tail

        return div

    def transform_sheet(self, sheet):
        """Transform a <sheet> element to a <div> element.
        """
        # Good G-d! Is this *really* the only way to copy an element(tree)?
        sheet2 = ET.XML(ET.tostring(sheet))

        # get all child->parent links
        cp = dict((c, p) for p in sheet2.getiterator() for c in p)

        blocks = sheet2.findall('ipython-block')
        for block in blocks:
            parent = cp[block]
            idx = list(parent).index(block)
            div = self.transform_block(block)
            parent[idx] = div

        figs = sheet2.findall('ipython-figure')
        for fig in figs:
            parent = cp[fig]
            idx = list(parent).index(fig)
            number = fig.get('number')
            logid = fig.get('logid', 'default-log')
            elem = self.notebook.get_from_log('figure', number, logid=logid)
            img = self.transform_figure(elem)
            parent[idx] = img

        sheet2.tag = 'div'
        # get rid of 'type' attribute
        sheet2.attrib.pop('type')
        return sheet2

    def format_sheet(self, sheet):
        """Format a <sheet> element to HTML text.
        """
        newsheet = self.transform_sheet(sheet)
        return ET.tostring(newsheet)

class HTMLFormatter(HTMLFragmentFormatter):
    """Formatter for HTML sheets to a full HTML file.
    """

    def get_template(self):
        """Get a template element that represents the HTML file.
        """
        html = ET.Element('html')
        head = ET.SubElement(html, 'head')
        body = ET.SubElement(html, 'body')
        style = ET.SubElement(head, 'style')
        style.text = self.CSS

        return html

    def transform_sheet(self, sheet):
        """Transform a <sheet> to a full <html> elemnt.
        """
        template = self.get_template()
        body = template.find('body')
        div = super(HTMLFormatter, self).transform_sheet(sheet)
        body.append(div)
        return template


