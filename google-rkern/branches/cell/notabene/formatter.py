"""Base Formatter class for notebooks.
"""

import textwrap

class Formatter(object):
    """Abstract base class implementing some useful common methods.

    Subclass and implement a format_sheet(sheet) method.
    """
    def __init__(self, notebook):
        self.notebook = notebook

    def indent(self, text, spaces):
        """Add a given number of spaces to the beginning of each line in text.
        """
        lines = text.strip().split('\n')
        tab = ' '*spaces
        lines = [tab + x for x in lines]
        lines.append('')
        return '\n'.join(lines)

    def format_input(self, elem, number):
        """Format an <input> element.
        """
        text = elem.text
        PS1 = 'In [%s]: ' % number
        PS2 = '...: '.rjust(len(PS1))
        lines = text.strip().split('\n')
        lines[0] = PS1 + lines[0]
        for i in xrange(1, len(lines)):
            lines[i] = PS2 + lines[1]
        lines.append('')
        return '\n'.join(lines)

    def format_output(self, elem, number):
        """Format an <output> element.
        """
        text = elem.text.strip()
        PS3 = 'Out[%s]: ' % number
        lines = text.split('\n')
        if len(lines) == 1:
            template = '%s%s\n'
        else:
            template = '%s\n%s\n'
        return template % (PS3, text)

    def format_figure(self, elem):
        """Format a <figure> element.
        """
        caption = elem.text
        if caption and caption.strip():
            caption = self.indent(textwrap.wrap(caption), 2)
            return 'Fig[%s]: %s\n\n%s\n' % (elem.attrib['number'],
                                            elem.attrib['filename'],
                                            caption)
        else:
            return 'Fig[%s]: %s\n' % (elem.attrib['number'],
                                      elem.attrib['filename'])

    def format_block(self, block):
        """Format an <ipython-block> tag.
        """
        texts = []
        logid = block.get('logid', 'default-log')
        for cell in block:
            number = cell.get('number')
            type = cell.get('type')
            elem = self.notebook.get_from_log(type, number, logid=logid)
            if type in ('input', 'special-input'):
                texts.append(self.format_input(elem, number))
            elif type in ('output',):
                texts.append(self.format_output(elem, number))
            else:
                raise NotImplementedError

        return '\n'.join(texts)


