#!/usr/bin/env python

import os
import subprocess
import tempfile

from lxml import etree as ET

from notabene import normal
from notabene import validate
from notabene.xmlutils import rdf, dc

class SubelemWrapper:
    """Abstract superclass for Cell getter and setter."""
    def __init__(self, propname):
        self.propname = propname #the name of the subelement in ob.element

class SubelemGetter(SubelemWrapper):
    """A template for getter functions to wrap an XML element."""
    def __call__(self, ob):
        element = ob.element.find(self.propname)
        if element is not None:
            return element.text
        else:
            return None

class SubelemSetter(SubelemWrapper):
    """A template for setter functions to wrap an XML element."""
    def __call__(self, ob, text): #now only works for setting text
        element = ob.element.find(self.propname)
        if element is None:
            element = ET.SubElement(ob.element, self.propname)
            element.text = text
        else:
            element.text = text


class Cell(object):
    #def __new__(
    #to check from logid & number if already exists
    
    def __init__(self, parent, number, element=None):
        #note: parent is a Log object, which has the 'root' as .element
        if element is None:
            self.element = ET.SubElement(parent.element, 'cell')
            self.number = number #sets the xml too via the property
        else:
            self.element = element
            assert self.number == number

    input  = property(SubelemGetter('input'),  SubelemSetter('input'))
    output = property(SubelemGetter('output'), SubelemSetter('output'))
    stdout = property(SubelemGetter('stdout'), SubelemSetter('stdout'))
    stderr = property(SubelemGetter('stderr'), SubelemSetter('stderr'))
    traceback = property(SubelemGetter('traceback'), SubelemSetter('traceback'))    

    def get_number(self):
        return int(self.element.attrib['number'])

    def set_number(self, num):
        s = str(num)
        if not s.isdigit():
            raise ValueError("number must be an integer")
        self.element.attrib['number'] = s
        #note: this does not update the cell index in the log!
        #so probably currently is safe only in the constructor, which is
        #given the index number by the Log.add <- Notebook.add_cell methods
    number = property(get_number,set_number)

    def get_sheet_tags(self, do_specials=False): #the special system is missing yet
        yield ET.Element('ipython-cell', type='input',
                         number=str(self.number))
        for tag in ('traceback', 'stdout', 'stderr', 'output'):
            if getattr(self, tag) is not None:
                yield ET.Element('ipython-cell', type=tag,
                                 number=str(self.number))

class Log(object):
    #one on the nbshell side there's IPythonLog
    #and we've talked about moving (parts of it) here
    def __init__(self, parent, logid, element=None):
        #note: parent is a Notebook object, which has the 'root' as .root
        self.id = logid
        self._cells = [] #it is not safe to manipulate this from outside
        #'cause of removals, may end up sparse - might make sense to use
        #something like http://inamidst.com/code/listdict.py
        if element is None:
            self.element = ET.SubElement(parent.root, 'ipython-log', id=logid)

        else:
            self.element = element
            for cellelem in self.element:
                self.add(int(cellelem.get('number')), cellelem)

    def add(self, number, element=None):
        if number >= len(self._cells): #is to be put at the end
            self._cells.extend([None] * (number - len(self._cells)))
            cell = Cell(self, number, element)
            self._cells.append(cell)
            return cell
        else:
            raise ValueError, 'a cell with number %d exists in log id %s' % (number, self.id)

    def __getitem__(self, position):
        if isinstance(position, slice):
            # Filter out None cells
            return [cell for cell in self._cells[position] if cell is not None]
        try:
            return self._cells[position]
        except:
            return None #to be consistent with slots
                        #where cells've been removed -- right?

    def __len__(self):
        return len(self._cells) #includes Nones i.e. is not the actual amount of
        # cells. Notebook.add_cell uses this currently to check if addition is to
        # the end of the list, so this can't be just changed to filter Nones out

    def __iter__(self):
        """Iterate over cells in the log and filter out None's."""
        cells = [cell for cell in self._cells if cell is not None]
        return iter(cells)

    def remove(self, number):
        cell = self._cells[number]
        if cell is None:
            raise IndexError
        
        if cell is self._cells[-1]: #if is last element
            self._cells.pop() #remove
            while self._cells[-1] is None: #if the previous, next. prev etc
                self._cells.pop() #remove all Nones at the end
        else:
            self._cells[number] = None #note: these gaps not handled everywhere
        self.element.remove(cell.element)

    def clear(self):
        self.element.clear()
        self._cells = []

    def get_code(self, specials=None):
        """Return the all of the code in the Log without the output.

        - specials (optional): unused currently; eventually it will be a boolean
          instructing the function to transform the special ipython commands
          into pure Python
        """
        lines = (x.input for x in self._cells if x is not None)
        return '\n'.join(lines)


class Notebook(object):
    """The core notebook object.

    Constructors:
    Notebook(name, root=None)
        name -- default base name for files
        root -- initialize from a properly formed root 'notebook' Element

    Notebook.from_string(name, data)
        data -- properly formed XML string

    Notebook.from_file(source, name=None)
        source -- filename or filelike object containing properly formed XML
            data
    """
    def __init__(self, name, root=None):
        self.name = name

        self.logs = {} #maps log-ids (strings) to logs,
                       #which now contain lists of cells.
                       #(for fast access)

        if root is None:
            self.root = ET.Element('notebook')
            self.head = ET.SubElement(self.root, 'head')
            self.add_log()
        else: 
            #reconstruct object structure from given xml
            self.root = root
            self.head = root.find('head')
            logelem = root.find('ipython-log')
            logid = logelem.get('id')
            self.logs[logid] = Log(self, logid, logelem) 

        self.tree = ET.ElementTree(self.root)
        self.xpath = ET.XPathEvaluator(self.tree)
        self.xpath.registerNamespace(rdf._prefix, rdf._url)


    def __eq__(self, other):
        """Determines if two Notebooks are equivalent to each other (more or
        less).

        Whitespace is ignored in certain contexts (see normal.py for the
        details). The order of top-level elements (head, ipython-log, sheet) are
        currently *not* ignored although it probably should be.
        """
        return normal.c14n(self.root) == normal.c14n(other.root)

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def from_string(cls, name, data):
        root = ET.fromstring(data)
        return cls(name, root=root)

    @classmethod
    def from_file(cls, source, name=None):
        if type(source) is str and name is None:
            name, ext = os.path.splitext(os.path.split(source)[-1])
        tree = ET.parse(source)
        return cls(name, root=tree.getroot())

    def check_errors(self):
        """Checks the notebook for syntax errors, returns (user-friendly) reports"""
        return validate.check_errors(ET.tostring(self.root))

    def add_log(self, id='default-log'):
        """Add a log element.

        id is a unique identifier. No other XML element in this file should have
        the same id.
        """
        others = self.root.xpath('//@id="%s"' % id)
        if others:
            raise ValueError('There are other elements with id="%s"' % id)
        log = Log(self, id) #this creates a subelement to self.root
        self.logs[id] = log
        return log

    def get_log(self, logid='default-log'):
        """Return a Log with the given logid.
        """
        if logid in self.logs:
            return self.logs[logid]
        else:
            raise ValueError('No log with id="%s"' % logid)

    def add_cell(self, number=None,  logid='default-log'):
        """Add an empty cell to the given log.

        - number (optional): add to the end by default
        """
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

    def add_figure(self, parent, filename, caption=None, type='png'):
        """Add a figure.
        """
        fig = ET.SubElement(parent, 'ipython-figure', filename=filename, type=type)
        if caption is not None:
            fig.text = caption

    def add_equation(self, parent, tex, title=None):
        """Add an equation (in tex). If given, a title is set."""
        equ = ET.SubElement(parent, 'ipython-equation', title=title, tex=tex)

    def write(self, file=None):
        """Write the notebook as XML out to a file.

        If file is None, then write to self.name+'.nbk'
        """
        if file is None:
            file = self.name + '.nbk'
        ET.ElementTree(self.root).write(file, encoding='utf-8')

    def write_formatted(self, name=None, format='html'):
        extensions = {'latex': '.tex',
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

        filename = os.path.abspath(base + ext)
        #could check if the given extension makes sense for the format

        from notabene import docbook
        formatter = docbook.DBFormatter(self)

        toPDF = False
        if format == 'pdf':
            format = 'latex' #we get pdf via latex for now
            toPDF = True
        doc = formatter.to_formatted(self.sheet, format)

        if toPDF:
            env = os.environ.copy()
            tmpfid, tmpfn = tempfile.mkstemp(suffix='.tex')
            tmpf = os.fdopen(tmpfid, 'w+b')
            try:
                doc.write(tmpf)
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
            doc.write(filename, 'utf-8')
            return filename

    def get_code(self, logid='default-log', specials=None):
        """Get the code from the specified Log.
        """
        return self.logs[logid].get_code(specials=specials)

    def default_sheet(self, logid='default-log'):
        log = self.logs[logid]
        sheet = ET.Element('sheet')
        block = ET.SubElement(sheet, 'ipython-block', logid=logid)
        for cell in log:
            #tzanko: This hides the 0 cell
            if cell.number > 0:
                for subcell in cell.get_sheet_tags():
                    block.append(subcell)
        return sheet

    def get_from_log(self, tag, number, logid='default-log'):
        #docbook.py and formatter.py use this. there is no unit test (yet)
        xpath = './ipython-log[@id="%s"]/cell[@number="%s"]/%s' % (logid,
            number, tag)
        elems = self.root.xpath(xpath)
        if elems:
            return elems[0]
        else:
            raise ValueError('No <%s> with number=%s in log "%s"' % (tag, number,
                logid))


    # XXX: We need to deal with multiple sheets.
    def get_sheet(self):
        try:
            return self.root.xpath('./sheet')[0] #assumes a single sheet
        except IndexError:
            return None #has no sheet

    def set_sheet(self, sheetelem):
        sheet = self.get_sheet()
        #XXX
        #remove old if different?
        #self.root.append(sheet)

    sheet = property(get_sheet, None)

    def get_title(self):
        if self.sheet is not None:
            #print "sheet in get_title:", self.sheet, ET.tostring(self.sheet)
            try:
                title = self.sheet.xpath('./title')[0] #single title per file
                #print ".. title:", title.text
                return title.text
            except IndexError:
                #print "no title"
                return None
        else:
            #print "no sheet in:", self, ET.tostring(self.root)
            return None
    title = property(get_title) #+setter

    def get_contents(self):
        if self.sheet is not None:
            #print "sheet in get_contents:", self.sheet, ET.tostring(self.sheet)
            sections = self.sheet.xpath('./section')
            #print "sections:", sections
            return sections

    contents = property(get_contents)

def main():
    import sys
    import os
    import optparse

    parser = optparse.OptionParser()
    parser.add_option('-f', '--format', dest='format', 
        help='output format', default='html', metavar='FORMAT')
    parser.add_option('-l', '--list-formats', dest='list_formats',
        help='list available formats', default=False, action='store_true')
    options, args = parser.parse_args()

    if options.list_formats:
        print """Available formats:
    html:  XHTML
    latex: LaTeX
    pdf:   PDF (via LaTeX, requires pdflatex(1))"""

    else:
        for file in args:
            base = os.path.splitext(file)[0]
            nb = Notebook.from_file(file)
            newfile = nb.write_formatted(base, options.format)
            print "%s -> %s" % (file, newfile)

if __name__ == '__main__':
    main()
