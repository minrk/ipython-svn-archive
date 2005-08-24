import py.test
from lxml import etree #as the API does not hide xml (yet?)
from notabene.notebook import Notebook, Cell

def test_new():
    nb = Notebook('test.nbk')
    return nb

def FAILStest_fromfile():
    nb = Notebook.from_file('../../test/tut-2.3.5-db.nbk') #how to deal with paths? perhaps with the ways to get relative to this

def test_fromstring(name='test', string='<a><b/></a>'):
    """Besides being a test, this is used by other test methods to hide possible api changes in Notebook.from_string."""
    nb = Notebook.from_string(name, string)
    return nb

def test_comparison():
    #are equal
    nb1 = test_fromstring('eq1') #, '<a><b></b></a>')
    nb2 = test_fromstring('eq2') #, '<a><b/></a>')
    assert nb1 == nb2
    assert not nb1 != nb2

    #inequality
    nb3 = test_fromstring('eq3', '<b><a/></b>')
    assert nb1 != nb3
    assert not nb1 == nb3

    #Tzanko:This fails
    #antont:not anymore!
    #and now also while the next passes, too
    nb4 = test_fromstring('nb4.nbk','<notebook><sheet></sheet></notebook>')
    nb5 = test_fromstring('nb5.nbk','<notebook>\n<sheet></sheet>\n</notebook>')
    assert nb4 == nb5

    #this was made to work with the old __eq__,
    #but now fails with the new normalization module.
    #based on the info by Tzanko recorded in Ticker 3, it's ok for this to fail
    nb6 = test_fromstring('nb6.nbk', '<notebook><sheet>a b c</sheet></notebook>')
    nb7 = test_fromstring('nb7.nbk', '<notebook><sheet>abc</sheet></notebook>')
    #FAILS assert not nb6 == nb7

    nb8 = test_fromstring('nb8.nbk', '<notebook><sheet><para><ipython-equation tex="e=mc^2"/></para></sheet></notebook>')
    nb9 = test_fromstring('nb9.nbk', '<notebook><sheet><para><ipython-equation tex="e=mc^3"/></para></sheet></notebook>')
    assert not nb8 == nb9

    #there may still be other cases,
    #but when adding failing tests
    #please consider the relevance to how
    #this feature is used.. (by nbshell)

    #based on additional comments in the ticket.. what should this be about?
    str10 = "<notebook>\n<sheet>\n<para>&lt;para&gt; elements can have <emphasis>mixed</emphasis> content.</para>\n</sheet>\n</notebook>"
    nb10 = test_fromstring('nb10.nbk', str10)
    str11 = "<notebook>\n<sheet>\n<para>&lt;para&gt; elements can have mixed content.</para>\n</sheet>\n</notebook>" #just -<emphasis>, as didn't get the point
    nb11 = test_fromstring('nb11.nbk', str11)
    assert nb10 != nb11

    #newlines in xml source for readability.
    #tho: this particular case can not happen with nbshell,
    #'cause it does not expose the input & output cell source, right?
    #and when editing .nbk source directly, equivalence check is not used?
    #surely with other tags (e.g. notebook-xml ones) it can happen w/ nbshell.
    str12 = "<input>\nfor i in range(10):\n    print i\n</input>"
    str13 = "<input>for i in range(10):\n    print i</input>"
    assert test_fromstring('nb12.nbk', str12) == test_fromstring('nb13.nbk', str13)
    #passed without changes to old __eq__
    #and also with the new normalization module

    #new from ticket3
    #fails with the new normalization module :/
    str14 = "<sheet>\n<para>text</para></sheet>"
    str15 = "<sheet><para>text</para></sheet>"
    assert test_fromstring('nb14.nbk', str14) == test_fromstring('nb15.nbk', str15)


def test_errcheck():
    nb = test_fromstring()
    assert nb.check_errors() is None

    #nb_err = test_fromstring('err', '<notebook>') #urgh of course already this fails
    from notabene.validate import check_errors
    print check_errors('<notebook>')


def test_sheet():
    nb = test_new()

    """Empty new nb has no sheet:"""
    assert nb.sheet is None

    sheet = nb.default_sheet()
    nb.root.append(sheet) #make a method for this? (hide root?)
    """Now the newly created sheet should be the current one:"""
    assert nb.sheet is sheet

def test_cell(elem=None, number=1):
    #should the Cell constructor take care of the xml too?
    #or perhaps make an add_cell to notebook?
    if elem is None:
        elem = etree.Element('cell', number=str(number))
        
    cell = Cell(elem)
    return cell
    
def OLDtest_log():
    """
    in nbshell ipnDocument:
    self.logs = {'default-log':IPythonLog.IPythonLog(self, self.notebook, 'default-log')}

    in nbshell iPythonLog:
    self.log = nbk.get_log(logid)

    in nbshell Sheet:
    logs = self.doc.logs
    for logid in logs.keys():
        for cell in (notebook.Cell(x) for x in logs[logid].log):
            self.UpdateOutput(logid, cell, update = False)
    """

    nb = test_new()    #Notebook.__init__ calls add_log which
    log = nb.get_log() #creates 'default-log' which comes here
    #as seen above, this behaviour is expected by nbshell.
    #(would even changing the name of the default break it?)

    """the new log should be empty.

    nbshell tests it like this in IPythonLog Append:
    l = len(self.log)
    if l != 0 :
        number = int(self.log[-1].attrib['number'])+1
    """
    assert len(log) == 0

    #cellelem, cell = test_cell()
    number = 1
    cellelem = etree.Element('cell', number=str(number)) 
    log.append(cellelem)
    assert len(log) == 1

    python_in = "3 // 2"
    python_out = "1"

    se_in = etree.SubElement(cellelem, 'input')
    se_in.text = python_in
    se_out = etree.SubElement(cellelem, 'output')
    se_out.text = python_out

    cell = test_cell(cellelem)

    #note: this appears to be unused (by nbshell)
    assert cell.get_input() == python_in
    #todo: cell.get_input(do_specials=True)
    #also get_sheet_tags seems to be unused by nbshell

    #modifications that require update.
    #at this point, the cell has an output, but no stdout nor stderr
    assert cell.element.find('stdout') is None
    assert cell.element.find('stderr') is None

    #so this code, from nbshell IPythonLog, creates those latter two
    #from nbshell.util import findnew #ZipImportError: bad local file header in /usr/lib/python2.4/site-packages/nbshell-0.1-py2.4.egg
    def findnew(element, tag):
        """Tries to find the tag in the element. If there is no such element,
        creates one"""
        el = element.find(tag)
        if el is None:
            el = etree.SubElement(element, tag)
        return el
    stdout = findnew(cell.element, 'stdout')
    stderr = findnew(cell.element, 'stderr')
    #now the cell has these new elements:
    assert cell.element.find('stdout') is not None
    assert cell.element.find('stderr') is not None

    #and must therefore be updated:
    #py.test.raises(AttributeError, cell.stdout)
    #py.test.raises(AttributeError, cell.stderr)
    assert not hasattr(cell, 'stdout')
    assert not hasattr(cell, 'stderr')
    cell.update() #used in nbshell IPythonLog __run
    #assert cell.stdout is stdout
    #assert cell.stderr is stderr
    assert hasattr(cell, 'stdout') #these are None. what's the use?
    assert hasattr(cell, 'stderr')

    sheet = nb.default_sheet()
    #assert nb.sheet is sheet #eek?
    ipblock = sheet.find('ipython-block') #above only one has been added(?)
    found = set()
    for ic in ipblock:
        if ic.tag == 'ipython-cell':
            found.add(ic.attrib['type'])
    assert found == set(['input', 'stdout', 'stderr', 'output'])

def test_log():
    nb = test_new() #adds a default log
    logelement = nb.get_log() #old way, to be removed?
    log = nb.newget_log()

    #using the default log via notebook methods
    py.test.raises(IndexError, "nb.get_cell(1)") #should not create anymore
    py.test.raises(ValueError, "nb.add_cell(15)") #can only add to end now
    cell = nb.add_cell(0) #is added to default log
    assert cell is nb.get_cell(0) #this should be the same one
    assert cell.input is None
    assert cell.output is None

    #multiple log support
    assert py.test.raises(ValueError, "nb.get_log('log2')") #nonexisting
    log2 = nb.add_log('log2')
    assert log2.element is nb.get_log('log2') #backwards compat. for nbshell
    assert log2 is nb.logs['log2'] #this is how Notebook does internally.
                                   #ok to expose to outside too?
    cell20 = nb.add_cell(0, 'log2')
    cell21 = log2.add(1) #also this is possible. ok?
    assert cell20 is nb.get_cell(0, 'log2')
    assert cell21 is nb.get_cell(1, 'log2')
    assert cell21.number == 1
    assert cell20 is log2[0] #again: Notebook does this. ok from outside?

    #back to default log, to test cell functionality
    python_in = "3 // 2"
    python_out = "1"

    cell.input = python_in
    cell.output = python_out
    assert cell.input == python_in
    assert cell.output == python_out
    #those must be the same in the underlying xml too:
    assert cell.element.find('input').text == python_in
    assert cell.element.find('output').text == python_out
    #nbshell also calls methods of xml elements
    #so they need to be exposed like this,
    #but at least in some cases the use should be limited to querying
    #.. altough manipulating some attributes is safe,
    #but e.g. changing the number attribute of a cell is not,
    #even though it is a property that wraps xml,
    #because Logs also have an index of them too.
    
    #note: the do-specials in original Cell not in the new system (yet)

    #should be standard elements too?
    assert cell.stdout is None
    assert cell.stderr is None

    #nbshell IPythonLog seems to use them as normal text elements
    stdouttext = "A printed thing came to stdout"
    stderrtext = "TestException came to stderr"
    cell.stdout = stdouttext
    cell.stderr = stderrtext
    assert cell.stdout == stdouttext
    assert cell.stderr == stderrtext
    assert cell.element.find('stdout').text == stdouttext
    assert cell.element.find('stderr').text == stderrtext

    #(default) sheet test
    sheet = nb.default_sheet()
    ipblock = sheet.find('ipython-block')
    found = set()
    for ic in ipblock:
        if ic.tag == 'ipython-cell':
            found.add(ic.attrib['type'])
    assert found == set(['input', 'stdout', 'stderr', 'output'])
    #cell.get_sheet_tags lacks tests

    #cell removal/deletion
    cell2 = nb.add_cell()
    cell3 = nb.add_cell()
    for number, cell in enumerate(log):
        assert number == cell.number
    number = cell2.number
    log.remove(number)
    assert log[number] is None #is not removed 'cause is in the middle
    numcells = log.element.xpath('./cell[@number=%s]' % number)
    assert len(numcells) == 0 #the cell was actually removed from xml

    #so far so good, but then all kinds of strange things start to happen:
    assert nb.get_cell(number) is None #does this make sense?
    #assert nb.get_last_cell() is None #this certainly does not!
    #so log.remove is fixed to handle it:
    lastcell = nb.get_last_cell()
    assert lastcell is log[-1] #nice, no? this also public..
    nb.remove_cell(lastcell.number)
    assert nb.get_last_cell() is not None
    for cell in log:
        print etree.tostring(cell.element)

    #should all trailing Nones be removed?
    #probably so, to make this succeed:
    cell2 = nb.add_cell()
    cell3 = nb.add_cell()
    cell4 = nb.add_cell()
    nb.remove_cell(cell2.number)
    nb.remove_cell(cell3.number)
    nb.remove_cell(cell4.number)
    assert nb.get_last_cell() is not None

    """
    16:16 < tzanko> I'm going to add additional rerunning fuctionality today and i
                need a fast way to get all the cells with a number larger than
                a given number. Probably the best way would be to implement
                list-like functionality for the log where log[5:10] would give
                me all the cells with 5<=cell.number<10
    """
    for _ in range(10):
        nb.add_cell()
    log[3:8] #sanity of the tampered slicing not really checked (yet)

    #filtering out Nones
    nb.remove_cell(5)
    for cell in log[3:8]:
        assert cell is not None


    

    
    

    
