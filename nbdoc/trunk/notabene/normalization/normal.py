from copy import deepcopy
from cStringIO import StringIO

from lxml import etree as ET

def stripnewlines(text):
    """These elements' text may have starting and trailing newlines that can be
    ignored.
    """
    if text is not None:
        return text.strip('\n')
    else:
        return None

def notext(text):
    """These elements should have no text, just children elements.
    """
    return None

data = [
    (notext, ['notebook', 'ipython-log', 'ipython-cell', 'sheet', 'cell',
              'ipython-block', 'head', 'meta', 'ipython-figure',
             ]),
    (stripnewlines, ['input', 'output', 
                     'traceback',  # ? might as well
                    #'stdin', 'stdout',  # not these; they should always be 
                                         # passed around verbatim
                    ]),
]

def normal(root):
    root = deepcopy(root)
    for normfunc, tags in data:
        for tag in tags:
            for elem in root.xpath('//%s' % tag):
                elem.text = normfunc(elem.text)
                for child in list(elem):
                    # lxml bug: for some reason, this iteration will
                    # sometimes fail if it's just "for child in elem:";
                    # looking into it, probably related to deepcopy
                    child.tail = normfunc(child.tail)
    return root

def c14n(root):
    root = normal(root)
    tree = ET.ElementTree(root)
    f = StringIO()
    tree.write_c14n(f)
    c14n_string = f.getvalue()
    f.close()
    return c14n_string
