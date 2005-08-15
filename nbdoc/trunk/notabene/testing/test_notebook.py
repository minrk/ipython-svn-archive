from notabene.notebook import Notebook

def test_new():
    nb = Notebook('test.nbk')
    return nb

## def test_fromfile():
##     nb = Notebook.from_file('../../test/tut-2.3.5-db.nbk') #how to deal with paths? from string would of course be nice here..

def test_sheet():
    nb = test_new()

    """Empty new nb has no sheet:"""
    assert nb.sheet is None

    sheet = nb.default_sheet()
    nb.root.append(sheet) #make a method for this? (hide root?)
    """Now the newly created sheet should be the current one:"""
    assert nb.sheet is sheet


    

    

    
