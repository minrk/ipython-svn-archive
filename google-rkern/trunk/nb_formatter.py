"""Base Formatter class for notebooks.
"""

class Formatter(object):
    """Abstract base class implementing some useful common methods.

    Subclass and implement a format_sheet(sheet) method.
    """
    def __init__(self, notebook):
        self.notebook = notebook
##        self.inputs = {}
##        self.special_inputs = {}
##        self.outputs = {}
##        self.figures = {}
##        for logid, log in notebook.logs.iteritems():
##            inputs = notebook._get_tag_dict('input', logid=logid)
##            for k, v in inputs.iteritems():
##                self.inputs[logid, k] = v
##            special_inputs = notebook._get_tag_dict('special-input',
##                logid=logid)
##            for k, v in special_inputs.iteritems():
##                self.special_inputs[logid, k] = v
##            outputs = notebook._get_tag_dict('output', logid=logid)
##            for k, v in outputs.iteritems():
##                self.outputs[logid, k] = v
##            figures = notebook._get_tag_dict('figure', logid=logid)
##            for k, v in figures.iteritems():
##                self.figures[logid, k] = v
##

    def indent(self, text, spaces):
        """Add a given number of spaces to the beginning of each line in text.
        """
        lines = text.strip().split('\n')
        tab = ' '*spaces
        lines = [tab + x for x in lines]
        lines.append('')
        return '\n'.join(lines)

    def format_input(self, elem):
        """Format an <input> element.
        """
        text = elem.text
        number = elem.attrib['number']
        PS1 = 'In [%s]: ' % number
        PS2 = '...: '.rjust(len(PS1))
        lines = text.strip().split('\n')
        lines[0] = PS1 + lines[0]
        for i in xrange(1, len(lines)):
            lines[i] = PS2 + lines[1]
        lines.append('')
        return '\n'.join(lines)

    def format_output(self, elem):
        """Format an <output> element.
        """
        text = elem.text.strip()
        number = elem.attrib['number']
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
                texts.append(self.format_input(elem))
            elif type in ('output',):
                texts.append(self.format_output(elem))
            else:
                raise NotImplementedError

        return '\n'.join(texts)


