#!/usr/bin/env python

import pprint
import string
import os

from elementtree import SimpleXMLWriter as SXW
#try:
#    from lxml import etree as ET
#except ImportError:
#    try:
#        import cElementTree as ET
#    except ImportError:
#        from elementtree import ElementTree as ET

# Okay, lxml's XPath support just wins handsdown here.
# We still need elementtree for SimpleXMLWriter *if* we still want the slightly
# prettier XML output.
from lxml import etree as ET

def _my_escape_cdata(s, encoding=None, replace=string.replace):
    if s.find('&') != -1 or s.find('<') != -1 or s.find('>') != -1:
        if s.find(']]>') == -1:
            s = '<!CDATA[[%s]]>' % s
        else:
            s = replace(s, '&', '&amp;')
            s = replace(s, '<', '&lt;')
            s = replace(s, '>', '&gt;')
    if encoding:
        try:
            return SXW.encode(s, encoding)
        except UnicodeError:
            return SXW.encode_entity(s)
    return s

SXW.escape_cdata = _my_escape_cdata

def write_element(elem, writer):
    writer.start(elem.tag, attrib=elem.attrib)
    writer.data('\n')
    if elem.text is not None:
        writer.data(elem.text)
    for child in elem:
        write_element(child, writer)
        if child.tail is not None:
            writer.data(child.tail)
    if (elem.tag in ('input', 'output', 'special-input') 
        and not elem.text.endswith('\n')):
        writer.data('\n')
    writer.end(elem.tag)
    writer.data('\n')

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

        ##self.logs = {}
        if root is None:
            self.root = ET.Element('notebook')
            self.head = ET.SubElement(self.root, 'head')
            self.add_log()
        else:
            self.root = root
            self.head = root.find('head')

            ##for log in self.root.findall('ipython-log'):
            ##    self.logs[log.get('logid')] = log

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
        ##self.logs[id] = log_element

    def get_log(self, logid='default-log'):
        elems = self.root.xpath('./log[@id="%s"]' % logid)
        if elems:
            return elems[0]
        else:
            raise ValueError('No log with id="%s"' % logid)

    def add_input(self, input, number, logid='default-log'):
        """Add an input element to a log.

        number is usually the integer corresponding to In[number].
        logid is the id of the log to add to.
        """
        log = self.get_log(logid)
        in_element = ET.SubElement(log, 'input', number=str(number))
        in_element.text = input

    def add_special_input(self, input, number, logid='default-log'):
        """Add an IPython special command like %magics and aliases.

        number is usually the integer corresponding to In[number].
        """
        log = self.get_log(logid)
        in_element = ET.SubElement(log, 'special-input',
            number=str(number))
        in_element.text = input

    def add_output(self, output, number, logid='default-log'):
        """Add an output element.

        number is usually the integer corresponding to Out[number].
        """
        log = self.get_log(logid)
        out_element = ET.SubElement(log, 'output', 
            number=str(number))
        out_element.text = self.get_str(output)

    def add_stdout(self, text, number, logid='default-log'):
        log = self.get_log(logid)
        stdout_element = ET.SubElement(log, 'stdout', number=str(number))
        stdout_element.text = text

    def add_stderr(self, text, number, logid='default-log'):
        log = self.get_log(logid)
        stderr_element = ET.SubElement(log, 'stderr', number=str(number))
        stderr_element.text = text

    def add_all_in_out(self, inlist, outdict, logid='default-log'):
        """Add all inputs and outputs from the In and Out variables in an
        ipython environment.
        """
        for i in xrange(1, len(inlist)):
            input = inlist[i]
            output = outdict.get(i, None)
            self.add_input(input, i, logid)
            if output is not None:
                self.add_output(output, i, logid)

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

    def add_figure(self, filename, number, caption=None, type='png', logid='default-log', **attribs):
        """Add a figure.
        """
        log = self.get_log(logid)
        fig = ET.SubElement(log, 'figure', filename=filename,
            number=str(number), type=type)
        fig.attrib.update(attribs)
        if caption is not None:
            fig.text = caption

    def write(self, file=None):
        """Write the notebook as XML out to a file.

        If file is None, then write to self.name+'.nbk'
        """
        if file is None:
            file = self.name + '.nbk'
        writer = SXW.XMLWriter(file)
        write_element(self.root, writer)

    def get_code(self, logid='default-log', specials=False):
        """Strip all non-input tags and format the inputs as text that could be
        executed in ipython.

        If specials is True, then replace all of the Python-formatted special
        commands as their original IPython form.
        """
        log = self.get_log(logid)
        inputs = list(log.findall('input'))
        if specials:
            special_elems = log.findall('special-input')
            d = self._get_tag_dict('special-input')
            for i, el in enumerate(inputs):
                inputs[i] = d.get(e.number, e)

        inputs.sort(lambda elem: int(elem.attrib['number']))
        return '\n'.join(x.text for x in inputs)

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
            self.add_output(arg, IP.outputcache.prompt_count)
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

        number = self.ipython_current_number()
        if filename is None:
            filename = '%s-%s.%s' % (self.name, number, type)

        savefig(filename)
        self.add_figure(os.path.split(filename)[-1], number, caption=caption, **attribs)

    def _get_tag_dict(self, tag, logid='default-log'):
        log = self.get_log(logid)
        d = {}
        elems = log.findall(tag)
        for elem in elems:
            d[elem.attrib['number']] = elem
        return d

    def default_sheet(self, format='rest', specials=True, figures=True,
        logid='default-log'):
        """Generate a default sheet that has all inputs and outputs.

        format is the name of the format of sheet. E.g. 'rest' or 'html'

        If specials is True, replace inputs that are ipython specials with their
            ipython form.
        If figures is True, include figures.
        """
        log = self.get_log(logid)
        outputd = self._get_tag_dict('output', logid=logid)
        figured = self._get_tag_dict('figure', logid=logid)
        speciald = self._get_tag_dict('special-input', logid=logid)
        stdoutd = self._get_tag_dict('stdout', logid=logid)
        stderrd = self._get_tag_dict('stderr', logid=logid)
        
        sheet = ET.Element('sheet', format=format)
        block = ET.SubElement(sheet, 'ipython-block', logid=logid)
        for inp in log.findall('input'):
            num = inp.attrib['number']
            if specials and num in speciald:
                ET.SubElement(block, 'ipython-cell', type='special-input', number=num)
            else:
                ET.SubElement(block, 'ipython-cell', type='input', number=num)
            if num in outputd:
                ET.SubElement(block, 'ipython-cell', type='output', number=num)
            if num in stdoutd:
                ET.SubElement(block, 'ipython-cell', type='stdout', number=num)
            if num in stderrd:
                ET.SubElement(block, 'ipython-cell', type='stderr', number=num)
            if num in figured:
                # add figures to the sheet, not the block
                ET.SubElement(sheet, 'ipython-figure',
                    ##filename=figured[num].attrib['filename'], 
                    number=num, logid=logid)
                # start a new block
                block = ET.SubElement(sheet, 'ipython-block', logid=logid)

        return sheet

    def get_from_log(self, tag, number, logid='default-log'):
        xpath = './log[@id="%s"]/%s[@number="%s"]' % (logid, tag, number)
        elems = self.root.xpath(xpath)
        if elems:
            return elems[0]
        else:
            raise ValueError('No <%s number=%s> in log "%s"' % (tag, number,
                logid))



def sheet_insert(sheet, elem, position):
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
    sheet = nb.root.find('sheet')
    if sheet is None:
        if len(sys.argv) >= 3:
            format = sys.argv[2]
        else:
            format = 'html'
        sheet = nb.default_sheet(format=format)
    format = sheet.get('format', 'html')

    if format == 'rest':
        from notabene import rest
        formatter = rest.ReSTFormatter(nb)
        outname = base + '.txt'
    elif format == 'html':
        from notabene import html
        formatter = html.HTMLFormatter(nb)
        outname = base + '.html'

    text = formatter.format_sheet(sheet)
    f = open(outname, 'w')
    f.write(text)

if __name__ == '__main__':
    main()
