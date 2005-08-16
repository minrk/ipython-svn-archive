#!/usr/bin/env python

import pprint
import string
import os

from StringIO import StringIO #to do (e.g.) write_c14n for nb.__eq__

from lxml import etree as ET

class Cell(object):
    def __init__(self, element):
        self.element = element
        
        self.tags = []

        self.update()

    def update(self, element=None):
        if element is not None:
            self.element = element
        else:
            element = self.element
        self.number = int(element.get('number'))
        for subelem in element:
            setattr(self, subelem.tag, subelem.text)
            self.tags.append(subelem.tag)

        # this doesn't delete attributes that were there previously

    def get_input(self, do_specials=False):
        if do_specials and hasattr(self, 'special'):
            return self.special
        else:
            return self.input

    def get_sheet_tags(self, do_specials=False):
        if do_specials and hasattr(self, 'special'):
            yield ET.Element('ipython-cell', type='special',
                number=str(self.number))
        else:
            yield ET.Element('ipython-cell', type='input',
                number=str(self.number))
        for tag in ('traceback', 'stdout', 'stderr', 'output'):
            if hasattr(self, tag):
                yield ET.Element('ipython-cell', type=tag,
                    number=str(self.number))




class Notebook(object):
    """The core notebook object.

    Constructors:
    Notebook(name, pretty=True, root=None, checkpoint=None)
        name -- default base name for files
        pretty -- boolean switch for pretty-formatting of output elements
        root -- initialize from a properly formed root 'notebook' Element
        checkpoint -- save notebook every checkpoint times during an IPython
            session or None

    Notebook.from_string(name, data, pretty=True, checkpoint=None)
        data -- properly formed XML string

    Notebook.from_file(source, name=None, pretty=True, checkpoint=None)
        source -- filename or filelike object containing properly formed XML
            data
    """
    def __init__(self, name, pretty=True, root=None, checkpoint=None):
        self.name = name
        self.pretty = pretty
        self.start_checkpointing(checkpoint)

        if root is None:
            self.root = ET.Element('notebook')
            self.head = ET.SubElement(self.root, 'head')
            self.add_log()
        else:
            self.root = root
            self.head = root.find('head')

    def __eq__(self, other):
        """As an answer to http://projects.scipy.org/ipython/ipython/ticket/3"""
        self_f = StringIO()
        other_f = StringIO()
        [ET.ElementTree(tree.root).write_c14n(f)
         for tree, f in [(self, self_f),
                         (other, other_f)]]
        return self_f.getvalue() == other_f.getvalue()

    @classmethod
    def from_string(cls, name, data, pretty=True):
        tree = ET.fromstring(data)
        return cls(name, pretty=pretty, root=tree.getroot())

    @classmethod
    def from_file(cls, source, name=None, pretty=True):
        if type(source) is str and name is None:
            name, ext = os.path.splitext(os.path.split(source)[-1])
        tree = ET.parse(source)
        return cls(name, pretty=pretty, root=tree.getroot())

    def get_str(self, obj):
        """Format string representation of object according to current
        preferences.
        """
        if self.pretty:
            return pprint.pformat(obj)
        else:
            return str(obj)

    def add_log(self, id='default-log'):
        """Add a log element.

        id is a unique identifier. No other XML element in this file should have
        the same id.
        """
        log_element = ET.SubElement(self.root, 'ipython-log', id=id)

    def get_log(self, logid='default-log'):
        elems = self.root.xpath('./ipython-log[@id="%s"]' % logid)
        if elems:
            return elems[0]
        else:
            raise ValueError('No log with id="%s"' % logid)

    def get_cell(self, number, logid='default-log'):
        log = self.get_log(logid)
        cells = log.xpath('./cell[@number=%s]' % number)
        if cells:
            return cells[0]
        else:
            return ET.SubElement(log, 'cell', number=str(number))

    def add_input(self, input, number, logid='default-log'):
        """Add an input element to a log.

        number is usually the integer corresponding to In[number].
        logid is the id of the log to add to.
        """
        cell = self.get_cell(number, logid)
        in_element = ET.SubElement(cell, 'input')
        in_element.text = input

    def add_special_input(self, input, number, logid='default-log'):
        """Add an IPython special command like %magics and aliases.

        number is usually the integer corresponding to In[number].
        """
        cell = self.get_cell(number, logid)
        in_element = ET.SubElement(cell, 'special')
        in_element.text = input

    def add_output(self, output, number, logid='default-log'):
        """Add an output element.

        output is the string representation of the object, not the object
            itself.
        number is usually the integer corresponding to Out[number].
        """
        cell = self.get_cell(number, logid)
        out_element = ET.SubElement(cell, 'output')
        out_element.text = output

    def add_stdout(self, text, number, logid='default-log'):
        cell = self.get_cell(number, logid)
        stdout_element = ET.SubElement(cell, 'stdout')
        stdout_element.text = text

    def add_stderr(self, text, number, logid='default-log'):
        cell = self.get_cell(number, logid)
        stderr_element = ET.SubElement(cell, 'stderr')
        stderr_element.text = text

    def add_meta(self, name, content, scheme=None):
        """Add metadata to the head element.

        name describes the kind of metadata.
        content is the actual value.
        scheme, if provided, describes the form of the content (e.g. a date or
            an int or whatever).

        The meta tag's usage is similar to that in HTML.
        """
        meta = ET.SubElement(self.head, 'meta', name=name, content=content)
        if scheme is not None:
            meta.set("scheme", scheme)

    def add_figure(self, parent, filename, caption=None, type='png', **attribs):
        """Add a figure.
        """
        fig = ET.SubElement(parent, 'ipython-figure', filename=filename, type=type)
        #fig.attrib.update(attribs)
        if caption is not None:
            fig.text = caption #hmn?

    def add_equation(self, parent, tex, title=None):
        """Add an equation (in tex). If given, a title is set."""
        equ = ET.SubElement(parent, 'ipython-equation', title=title, tex=tex)
       

    def write(self, file=None):
        """Write the notebook as XML out to a file.

        If file is None, then write to self.name+'.nbk'
        """
        if file is None:
            file = self.name + '.nbk'
        ET.ElementTree(self.root).write(file)

    def write_formatted(self, name=None, format='html'):
        name = name or self.name
        extensions = {'latex': '.tex',
                      'html': '.html',
                      }
        filename = name + extensions.get(format, '.'+format)

        from notabene import docbook
        formatter = docbook.DBFormatter(self)
        doc = formatter.to_text(self.sheet, format)

        doc.write(outname, 'utf-8') #docbook html xsl uses non-ascii chars

    def get_code(self, logid='default-log', specials=False):
        """Strip all non-input tags and format the inputs as text that could be
        executed in ipython.

        If specials is True, then replace all of the Python-formatted special
        commands as their original IPython form.
        """
        log = self.get_log(logid)
        cells = sorted((Cell(x) for x in log), key=lambda x: x.number)
        return '\n'.join(cell.get_input(specials) for cell in cells)

    def start_checkpointing(self, checkpoint=10):
        """Start checkpointing.
        """
        self.checkpoint = checkpoint

    def stop_checkpointing(self):
        """Stop checkpointing.
        """
        self.checkpoint = None

    def ipython_monkeypatch(self, IP):
        """Abandon all sanity, ye who enter here.

        In [1]: import notabene; nb = notabene.Notebook()
        In [2]: nb.ipython_monkeypatch(__IP)
        """

        # new input hook for Python source
        # also, trap stdout, stderr
        IP._runsource = IP.runsource
        def runsource(source, filename="<input>", symbol="single"):
            code = IP._runsource(source, filename=filename, symbol=symbol)
            if code == False:
                # it's complete
                number = IP.outputcache.prompt_count
                self.add_input(source, number)
                if (self.checkpoint is not None and 
                    not IP.outputcache.prompt_count % self.checkpoint):
                    self.write()
            return code
        IP.runsource = runsource

        # new input hook for aliases
        IP._handle_alias = IP.handle_alias
        def handle_alias(line,continue_prompt=None,
             pre=None,iFun=None,theRest=None):
             line_out = IP._handle_alias(line, continue_prompt, pre, iFun,
                 theRest)
             number = IP.outputcache.prompt_count
             self.add_special_input(line, number)
             return line_out
        IP.handle_alias = handle_alias

        # new input hook for shell escapes
        IP._handle_shell_escape = IP.handle_shell_escape
        def handle_shell_escape(line, continue_prompt=None,
            pre=None,iFun=None,theRest=None):
            line_out = IP._handle_shell_escape(line, continue_prompt, pre, 
                iFun, theRest)
            number = IP.outputcache.prompt_count
            self.add_special_input(line, number)
            return line_out
        IP.handle_shell_escape = handle_shell_escape

        # new input hook for magics
        IP._handle_magic = IP.handle_magic
        def handle_magic(line, continue_prompt=None,
            pre=None,iFun=None,theRest=None):
            line_out = IP._handle_magic(line, continue_prompt, pre, 
                iFun, theRest)
            number = IP.outputcache.prompt_count
            self.add_special_input(line, number)
            return line_out
        IP.handle_magic = handle_magic

        # new input hook for autocall lines
        IP._handle_auto = IP.handle_auto
        def handle_auto(line, continue_prompt=None,
            pre=None,iFun=None,theRest=None):
            line_out = IP._handle_auto(line, continue_prompt, pre, 
                iFun, theRest)
            number = IP.outputcache.prompt_count
            self.add_special_input(line, number)
            return line_out
        IP.handle_auto = handle_auto

        # new input hook for helps
        IP._handle_help = IP.handle_help
        def handle_help(line, continue_prompt=None,
            pre=None,iFun=None,theRest=None):
            line_out = IP._handle_help(line, continue_prompt, pre, 
                iFun, theRest)
            number = IP.outputcache.prompt_count
            self.add_special_input(line, number)
            return line_out
        IP.handle_help = handle_help

        # new output hook
        IP.outputcache._update = IP.outputcache.update
        def update(arg):
            IP.outputcache._update(arg)
            self.add_output(self.get_str(arg), IP.outputcache.prompt_count)
        IP.outputcache.update = update

        IP.esc_handlers = {IP.ESC_PAREN:handle_auto,
                           IP.ESC_QUOTE:handle_auto,
                           IP.ESC_QUOTE2:handle_auto,
                           IP.ESC_MAGIC:handle_magic,
                           IP.ESC_HELP:handle_help,
                           IP.ESC_SHELL:handle_shell_escape,
                          }

        self.IP = IP

        # I'm *so* going to Hell for this.

    def ipython_unmonkey(self):
        """Undo the evil hacks perpetrated by ipython_monkeypatch().
        """
        IP = self.IP
        if hasattr(IP, '_runsource'):
            IP.runsource = IP._runsource
            IP.handle_alias = IP._handle_alias
            IP.handle_help = IP._handle_help
            IP.handle_auto = IP._handle_auto
            IP.handle_magic = IP._handle_magic
            IP.handle_shell_escape = IP._handle_shell_escape
            IP.outputcache.update = IP.outputcache._update

            IP.esc_handlers = {IP.ESC_PAREN:IP._handle_auto,
                               IP.ESC_QUOTE:IP._handle_auto,
                               IP.ESC_QUOTE2:IP._handle_auto,
                               IP.ESC_MAGIC:IP._handle_magic,
                               IP.ESC_HELP:IP._handle_help,
                               IP.ESC_SHELL:IP._handle_shell_escape,
                              }

    def ipython_current_number(self):
        """Get the current prompt number.
        """
        return self.IP.outputcache.prompt_count

    def pylab_savefig(self, filename=None, caption=None, type='png', **attribs):
        """Save the current pylab figure to a file and inserts a figure element
        into the notebook.
        """
        from matplotlib.pylab import savefig

        #number = self.ipython_current_number()
        parent = self.sheet
        if filename is None:
            filename = '%s.%s' % (self.name, type)

        savefig(filename)
        print "saved", filename
        self.add_figure(parent, os.path.split(filename)[-1], caption=caption, **attribs)

    def _get_tag_dict(self, tag, logid='default-log'):
        log = self.get_log(logid)
        d = {}
        elems = log.findall(tag)
        for elem in elems:
            d[elem.attrib['number']] = elem
        return d

    def default_sheet(self, specials=True, figures=True,
        logid='default-log'):
        """Generate a default sheet that has all inputs and outputs.

        If specials is True, replace inputs that are ipython specials with their
            ipython form.
        If figures is True, include figures.
        """
        log = self.get_log(logid)
        cells = sorted((Cell(x) for x in log), key=lambda x: x.number)
        figured = dict((int(x.get('number')), x) for x in log.xpath('./figure'))
        
        sheet = ET.Element('sheet')
        block = ET.SubElement(sheet, 'ipython-block', logid=logid)
        for cell in cells:
            for subcell in cell.get_sheet_tags(specials):
                block.append(subcell)

            if figures: #and cell.number in figured:
                # add figures to the sheet, not the block
                #ET.SubElement(sheet, 'ipython-figure') #XXX why this?
                # start a new block
                block = ET.SubElement(sheet, 'ipython-block', logid=logid)

        return sheet

    def get_from_log(self, tag, number, logid='default-log'):
        xpath = './ipython-log[@id="%s"]/cell[@number="%s"]/%s' % (logid,
            number, tag)
        elems = self.root.xpath(xpath)
        if elems:
            return elems[0]
        else:
            raise ValueError('No <%s> with number=%s in log "%s"' % (tag, number,
                logid))

    def get_sheet(self):
        try:
            return self.root.xpath('./sheet')[0] #assumes a single sheet
        except IndexError:
            return None #has no sheet
    sheet = property(get_sheet, None)


def sheet_insert(sheet, elem, position):
    """For adding an element based on the character-counted position.

    Is this really useful? So far unused.
    """
    #and what does this actually do?
    texts = [sheet.text]
    texts.extend(x.tail for x in sheet)
    elements = [sheet]
    elements.extend(sheet)
    length = 0
    old_length = 0
    for i, s in enumerate(texts):
        length += len(s)
        if position <= length:
            pre = s[:position-old_length]
            post = s[position-old_length:]
            sheet.insert(i, elem)
            elements[i].text = pre
            elem.text = post
            return

    raise ValueError("position > text length")

def main():
    import sys
    import os
    file = sys.argv[1]
    base = os.path.splitext(file)[0]
    nb = Notebook.from_file(file)

    if len(sys.argv) >= 3:
        format = sys.argv[2]
    else:
        format = 'html'
    if not sheet: #is this needed? not used now anymore.
        sheet = nb.default_sheet()

    nb.write_formatted(base, format)

if __name__ == '__main__':
    main()
