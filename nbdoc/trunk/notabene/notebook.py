#!/usr/bin/env python

import pprint
import string
import os
from cStringIO import StringIO #to do (e.g.) write_c14n for nb.__eq__ .

from lxml import etree as ET

from notabene.normalization import normal
from notabene import validate #for Notebook.check_errors

#this specials system that was in the (unused) cell not reimplemented yet
##     def get_input(self, do_specials=False):
##         if do_specials and hasattr(self, 'special'):
##             return self.special
##         else:
##             return self.input

##     def get_sheet_tags(self, do_specials=False):
##         if do_specials and hasattr(self, 'special'):
##             yield ET.Element('ipython-cell', type='special',
##                 number=str(self.number))
##         else:
##             yield ET.Element('ipython-cell', type='input',
##                 number=str(self.number))
##         for tag in ('traceback', 'stdout', 'stderr', 'output'):
##             if hasattr(self, tag):
##                 yield ET.Element('ipython-cell', type=tag,
##                     number=str(self.number))

class SubelemWrapper:
    """abstract superclass for getter and setter"""
    def __init__(self, propname):
        self.propname = propname #the name of the subelement in ob.element

class SubelemGetter(SubelemWrapper):
    """a template for getter functions to wrap an xml element"""
    def __call__(self, ob):
        in_element = ob.element.find(self.propname)
        if in_element is not None:
            return in_element.text
        else:
            return None

class SubelemSetter(SubelemWrapper):
    """a template for setter functions to wrap an xml element"""
    def __call__(self, ob, text): #now only works for setting text
        in_element = ob.element.find(self.propname)
        if in_element is None:
            in_element = ET.SubElement(ob.element, self.propname)
        in_element.text = text


class Cell(object):
    def __init__(self, element):
        #to be replaced by newinit
        self.element = element

    @classmethod
    def newinit(cls, parent, number):
        #__init__ will have this signature
        #(if/)when nbshell does not suppose the current anymore,
        #note: parent is a Log object, which has the 'root' as .element
        element = ET.SubElement(parent.element, 'cell')
        instance = cls(element)
        instance.number = number #sets the xml too via the property
        return instance

    input  = property(SubelemGetter('input'),  SubelemSetter('input'))
    output = property(SubelemGetter('output'), SubelemSetter('output'))
    stdout = property(SubelemGetter('stdout'), SubelemSetter('stdout'))
    stderr = property(SubelemGetter('stderr'), SubelemSetter('stderr'))
    traceback = property(SubelemGetter('traceback'), SubelemSetter('traceback'))    
    def get_number(self):
        return int(self.element.attrib['number'])
    def set_number(self, num):
        s = str(num)
        assert s.isdigit()
        self.element.attrib['number'] = s
        #note: this does not update the cell index in the log!
        #so probably currently is safe only in the constructor, which is
        #given the index number by the Log.add <- Notebook.add_cell methods
    number = property(get_number,set_number)

    def get_input(self, do_specials=False):
        raise RuntimeError, "unimplemented"
    
    def get_sheet_tags(self, do_specials=False): #the special system is missing yet
        yield ET.Element('ipython-cell', type='input',
                         number=str(self.number))
        for tag in ('traceback', 'stdout', 'stderr', 'output'):
            if getattr(self, tag) is not None:
                yield ET.Element('ipython-cell', type=tag,
                                 number=str(self.number))

def slicerange(s):
    #from http://inamidst.com/code/listdict.py for Log.__getitem
    if (not isinstance(s, slice)) or (s.start == s.stop): 
        raise ValueError("Expected non-zero sized slice object")
    return xrange(s.start, s.stop, s.step or 1)

class Log(object):
    #one on the nbshell side there's IPythonLog
    #and we've talked about moving (parts of it) here
    def __init__(self, parent, logid):
        #note: parent is a Notebook object, which has the 'root' as .root
        self.id = logid
        self.element = ET.SubElement(parent.root, 'ipython-log', id=logid)
        self._cells = [] #it is not safe to manipulate this from outside
        #'cause of removals, this may end up sparse - might make sense to use
        #something like http://inamidst.com/code/listdict.py

    def add(self, number):
        if number == len(self._cells): #is to be put at the end
            #cell = Cell(self, number) #use this when nbshell is refactored
            cell = Cell.newinit(self, number) #temporary for transition
            self._cells.append(cell) #always adds to end
            #self.element.append(cell.element) #already became a subelement
            #seems that that append call would have no effect.
            return cell
                
        else:
            try:
                self._cells[number]
                raise ValueError, 'a cell with number %d exists in log id %s' % (number, self.id)
            except IndexError:
                if number > len(self._cells):
                    raise ValueError, "can only add at the end now. that will be fixed if needed."
                else:
                    raise RuntimeError, "unknown error when adding cell with number %d to log %s" % (number, self.id)

    def __getitem__(self, position):
        if isinstance(position, slice):
            if position.start != position.stop:
                """Filters out None cells"""
                return [x for x in self._cells[position] if x is not None]
                #retrieves _cells[i] twice but probably still pretty fast
            #if this is bad or slow can be also removed and let users filter
        return self._cells[position]

    def __len__(self):
        return len(self._cells) #includes Nones i.e. is not the actual amount of cells. Notebook.add_cell uses this currently to check if addition is to the end of the list, so this can't be just changed to filter Nones out

    def __iter__(self):
        """for iterating cells in the log. filters out Nones."""
        cells = [cell for cell in self._cells if cell is not None]
        return iter(cells)

    def remove(self, number):
        cell = self._cells[number]
        if cell is self._cells[-1]: #if is last element
            self._cells.pop() #remove
            while self._cells[-1] is None: #if the previous, next. prev etc
                self._cells.pop() #remove all Nones at the end
        else:
            self._cells[number] = None #XXX these gaps not handled everywhere
        self.element.remove(cell.element)

#from notes, regarding Sheet.InsertElement and related dict
# <@tzanko> well in the sheet i store a dictionary Sheet.cell2sheet
# <@tzanko> I need the dictionary, because I need a fast way to get all the
#           <ipython-cell> elements, that correspond to a given cell in a
#           log
#so what kind of method is needed? probably here in log, returning cells or cell elements or their contents..?


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

        self.logs = {} #maps log-ids (strings) to logs,
                       #which now contain lists of cells.
                       #(for fast access)

        if root is None:
            self.root = ET.Element('notebook')
            self.head = ET.SubElement(self.root, 'head')
            self.add_log()
        else:
            self.root = root
            self.head = root.find('head')

    def __eq__(self, other):
        """As an answer to http://projects.scipy.org/ipython/ipython/ticket/3

        note that 'equivalence' here means semantical(?) equivalence,
        i.e. not that the xml source is the same, but the notebook it describes.
        in addition to the standard canoninalization,
        white space & newlines are ignored.
        """

        return normal.c14n(self.root) == normal.c14n(other.root)
        #preprocesses several cases before doing standard canoninalization

    def __ne__(self, other):
        return not self.__eq__(other)

    #how do the from* methods actually behave w.r.t to Cells and self.logs?
    #perhaps some initial processing is needed now, when
    #the objects here don't just access xml but are used as structure too..
    @classmethod
    def from_string(cls, name, data, pretty=True):
        root = ET.fromstring(data)
        return cls(name, pretty=pretty, root=root)

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

    def check_errors(self):
        """Checks the notebook for syntax errors, returns (user-friendly) reports"""
        return validate.check_errors(ET.tostring(self.root))

    def add_log(self, id='default-log'):
        """Add a log element.

        id is a unique identifier. No other XML element in this file should have        the same id.
        """
        #should the uniqueness of the id be checked here?
        log = Log(self, id) #this creates a subelement to self.root
        self.logs[id] = log
        return log

    def get_log(self, logid='default-log'):
        #elems = self.root.xpath('./ipython-log[@id="%s"]' % logid)
        #if elems:
        #    return elems[0]
        if logid in self.logs:
            #return self.logs[logid]
            return self.logs[logid].element #callers probably expect that now
        #this is not used by the internal methods that use the Log class,
        #but only from external (in nbshell) that don't know that class yet.
        else:
            raise ValueError('No log with id="%s"' % logid)

    def newget_log(self, logid='default-log'):
        #useful for getting a default log without id,
        #even if/when self.logs is exposed for id-using getting of logs.
        #to replace current get_log when that is not used anymore
        if logid in self.logs:
            return self.logs[logid]
        else:
            raise ValueError('No log with id="%s"' % logid)

    def oldget_cell(self, number, logid='default-log'):
        #note: Tzanko considers this too slow for nbshell
        log = self.get_log(logid)
        cells = log.xpath('./cell[@number=%s]' % number)
        if cells:
            return cells[0]
        else:
            return ET.SubElement(log, 'cell', number=str(number))

    def add_cell(self, number=None,  logid='default-log'):
        log = self.logs[logid]
        if number is None: #add to end by default
            #not used by nbshell currently,
            #but handy for at least tests..
            number = len(log)
        cell = log.add(number)
        return cell

    def get_cell(self, number, logid='default-log'):
        log = self.logs[logid]
        return log[number]

    def get_last_cell(self, logid='default-log'):
        log = self.logs[logid]
        return log[-1]

    def remove_cell(self, number, logid='default-log'):
        log = self.logs[logid]
        log.remove(number) #now a method of the Log class
        
# These are Cell operations now.
# Would they still be useful as Notebook methods too?
# Can be easily changed to work with the new Cell if needed.
##     def add_input(self, input, number, logid='default-log'):
##         """Add an input element to a log.

##         number is usually the integer corresponding to In[number].
##         logid is the id of the log to add to.
##         """
##         cell = self.get_cell(number, logid)
##         in_element = ET.SubElement(cell, 'input')
##         in_element.text = input

##     def add_special_input(self, input, number, logid='default-log'):
##         """Add an IPython special command like %magics and aliases.

##         number is usually the integer corresponding to In[number].
##         """
##         cell = self.get_cell(number, logid)
##         in_element = ET.SubElement(cell, 'special')
##         in_element.text = input

##     def add_output(self, output, number, logid='default-log'):
##         """Add an output element.

##         output is the string representation of the object, not the object
##             itself.
##         number is usually the integer corresponding to Out[number].
##         """
##         cell = self.get_cell(number, logid)
##         out_element = ET.SubElement(cell, 'output')
##         out_element.text = output

##     def add_stdout(self, text, number, logid='default-log'):
##         cell = self.get_cell(number, logid)
##         stdout_element = ET.SubElement(cell, 'stdout')
##         stdout_element.text = text

##     def add_stderr(self, text, number, logid='default-log'):
##         cell = self.get_cell(number, logid)
##         stderr_element = ET.SubElement(cell, 'stderr')
##         stderr_element.text = text

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
        extensions = {'latex': '.tex', #should .latex be allowed like .htm is?
                      'html': '.html',
                      'doshtml': '.htm', #to allow specifying it explicitly
                      'pdf': '.pdf',
                      }

        if name is not None:
            base, ext = os.path.splitext(name) #allows giving also ext in name
            if ext not in extensions.values():
                #probably the name has a dot in it, like 'tut-2.3.5-db'
                base = name
                ext = False

        else:
            base = self.name
            ext = False #os.path.splitext may have put '' which is False

        if not ext:
            ext = extensions.get(format, '.'+format)

        filename = base + ext
        #could check if the given extension makes sense for the format

        from notabene import docbook
        formatter = docbook.DBFormatter(self)

        toPDF = False
        if format == 'pdf':
            format = 'latex' #we get pdf via latex for now
            toPDF = True
        doc = formatter.to_formatted(self.sheet, format)

        if toPDF:
            tmpnam = os.tmpnam() #not nice on windows (uses root dir)
            doc.write(tmpnam) #'/tmp/' + name + '.tex')
            print os.popen("pdflatex --jobname=%s %s" % (name, tmpnam)).read()
            return name+'.pdf' #in cwd, no option to change in pdflatex (?)
            #XXX

        else:
            doc.write(filename, 'utf-8') #docbook html xsl uses non-ascii chars
            return filename

    def oldget_code(self, logid='default-log', specials=False):
        """Strip all non-input tags and format the inputs as text that could be
        executed in ipython.

        If specials is True, then replace all of the Python-formatted special
        commands as their original IPython form.
        """
        log = self.get_log(logid)
        cells = sorted((Cell(x) for x in log), key=lambda x: x.number)
        return '\n'.join(cell.get_input(specials) for cell in cells)

    def get_code(self, logid='default-log', specials=False):
        #XXX new for the new cell and log system, untested
        log = self.logs[logid]
        return '\n'.join(cell.get_input(specials) for cell in log)

    def start_checkpointing(self, checkpoint=10):
        """Start checkpointing.
        """
        self.checkpoint = checkpoint

    def stop_checkpointing(self):
        """Stop checkpointing.
        """
        self.checkpoint = None

    def ipython_monkeypatch(self, IP):
        #not maintained since moving over from google-rkern,
        #where there probably still is a working version.
        #nbshell does not use it, but perpaps this would be
        #still nice to have for using straight from normal ipython shell?
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
        #is this used? fixing for the new system..
        log = self.logs[logid]
        d = {}
        elems = log.element.findall(tag)
        for elem in elems:
            d[elem.attrib['number']] = elem
        return d

    def olddefault_sheet(self, specials=True, figures=True,
        logid='default-log'):
        """Generate a default sheet that has all inputs and outputs.

        If specials is True, replace inputs that are ipython specials with their
            ipython form.
        If figures is True, include figures.
        """
        log = self.get_log(logid)
        cells = sorted((Cell(x) for x in log), key=lambda x: x.number)
        figures = dict((int(x.get('number')), x) for x in log.xpath('./figure'))
        
        sheet = ET.Element('sheet')
        block = ET.SubElement(sheet, 'ipython-block', logid=logid)
        for cell in cells:
            for subcell in  cell.get_sheet_tags(specials):
                print "DEFAULT SHEET: appending", subcell
                block.append(subcell)

            #if figures: #and cell.number in figured:
                # add figures to the sheet, not the block
                #ET.SubElement(sheet, 'ipython-figure') #XXX why this?
                # start a new block
                #block = ET.SubElement(sheet, 'ipython-block', logid=logid)

        return sheet

    def default_sheet(self):
        logid='default-log'
        log = self.logs[logid]
        sheet = ET.Element('sheet')
        block = ET.SubElement(sheet, 'ipython-block', logid=logid)
        for cell in log:
            #dbg
            print "*NEW*DEFAULT SHEET: cell", cell
            for subcell in cell.get_sheet_tags():
                block.append(subcell)
        return sheet
            

    def get_from_log(self, tag, number, logid='default-log'):
        #docbook.py and formatter.py use this. XXX check if works after changes
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

    filename = nb.write_formatted(base, format)
    print "Wrote result to", filename

if __name__ == '__main__':
    main()
