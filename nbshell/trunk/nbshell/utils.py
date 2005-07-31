""" Utility functions and classes """

#This method is temporary until notebook.py is fixed

from notabene import notebook
from notabene.notebook import *

def get_sheet_tags(self, do_specials=False):
    if do_specials and hasattr(self, 'special'):
        yield ET.Element('ipython-special',
            number=str(self.number))
    else:
        yield ET.Element('ipython-input',
            number=str(self.number))
    for tag in ('traceback', 'stdout', 'stderr', 'output'):
        if hasattr(self, tag):
            yield ET.Element('ipython-%s'%tag,
                number=str(self.number))
notebook.Cell.get_sheet_tags = get_sheet_tags
del notebook

