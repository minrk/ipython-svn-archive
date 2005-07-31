""" Utility functions and classes """

#This method is temporary until notebook.py is fixed
from notabene import notebook
from notabene.notebook import *
def default_sheet(self, specials=True, figures=True,
                  logid='default-log'):
    """Generate a default sheet that has all inputs and outputs.

    If specials is True, replace inputs that are ipython specials with their
        ipython form.
    If figures is True, include figures.
    """
    log = self.get_log(logid)
    cells = sorted((Cell(x) for x in log), lambda x: x.number)
    figured = dict((int(x.get('number')), x) for x in log.xpath('./figure'))
    
    sheet = ET.Element('sheet')
    block = ET.SubElement(sheet, 'ipython-block', logid=logid)
    for cell in cells:
        for subcell in cell.get_sheet_tags(specials):
            block.append(subcell)

        if figures and cell.number in figured:
            # add figures to the sheet, not the block
            ET.SubElement(sheet, 'ipython-figure',
                number=str(cell.number), logid=logid)
            # start a new block
            block = ET.SubElement(sheet, 'ipython-block', logid=logid)

    return sheet

notebook.Notebook.default_sheet = default_sheet
del notebook

