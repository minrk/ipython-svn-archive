"""Formatter object for reST notebook sheets.
"""

from nb_formatter import Formatter

class ReSTFormatter(Formatter):
    """Formatter for reST output.
    """
    def format_block(self, block):
        """Format an <ipython-block> element.
        """
        # Just need to take the raw text from Formatter ...
        text = Formatter.format_block(self, block)
        # indent it a bit ...
        text = self.indent(text, 2)
        # and slap a raw marker in front.
        # XXX: make a docutils .. ipython-block:: directive
        text = '::\n\n' + text
        return text

    def format_figure(self, elem):
        """Format a <figure> element.
        """
        return '.. image:: %s\n' % elem.attrib['filename']

    def format_sheet(self, sheet):
        """Format a reST sheet.

        XXX: raise ValueError if sheet's type is not rest?
        """
        if sheet.text is None:
            texts = ['']
        else:
            texts = [sheet.text]
        for elem in sheet:
            # find indentation of the line where this tag starts.
            last = texts[-1]
            last_line = last[last.rfind('\n')+1:]
            spaces = len(last_line) - len(last_line.lstrip())
            if elem.tag == 'ipython-block':
                text = self.format_block(elem)
            elif elem.tag == 'ipython-figure':
                text = self.format_figure(elem)
            text = self.indent(text, spaces)
            texts.append(text)
            if elem.tail is not None:
                texts.append(elem.tail)

        return '\n'.join(texts)

