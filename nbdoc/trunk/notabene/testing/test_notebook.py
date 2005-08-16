from lxml import etree #as the API does not hide xml (yet?)
from notabene.notebook import Notebook, Cell

def test_new():
    nb = Notebook('test.nbk')
    return nb

def FAILStest_fromfile():
    nb = Notebook.from_file('../../test/tut-2.3.5-db.nbk') #how to deal with paths? perhaps with the ways to get relative to this

def test_fromstring(name='test', string='<a><b/></a>'):
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
    #antont:not anymore! but what does, that i do not know..
    nb1 = Notebook.from_string('nb1.nbk','<notebook><sheet></sheet></notebook>')
    nb2 = Notebook.from_string('nb1.nbk','<notebook>\n<sheet></sheet>\n</notebook>')
    assert nb1 == nb2

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
    
def test_log():
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

    #XXX modifications that require update coming here
    cell.update() #used in nbshell IPythonLog __run
    
    
    

    

    
    


    
    
    
    
    

    
    
    
    
    
    

    

    

    
