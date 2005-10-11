#!/usr/bin/env python
from lxml import etree as ET

from notabene.xmlutils import nsmap, ip, db

class Convert1to1_1(object):
    fromto = ("1", "1.1")
    tagmap = {'notebook': ip.notebook,
              'head': ip.head,
              'meta': ip.meta,
              'ipython-log': ip.log,
              'cell': ip.cell,
              'input': ip.input,
              'output': ip.output,
              'traceback': ip.traceback,
              'stdout': ip.stdout,
              'stderr': ip.stderr,
              'sheet': ip.sheet,
              'ipython-block': ip.block,
              'ipython-cell': ip.cell,
              'ipython-figure': ip.figure,
              'ipython-equation': ip.equation,
              'ipython-inlineequation': ip.inlineequation,
              'para': db.para,
              'section': db.section,
              'title': db.title,
              'emphasis': db.emphasis,
              'programlisting': db.programlisting,
              'code': db.code,
              'footnote': db.footnote,
              'listitem': db.listitem,
              'itemizedlist': db.itemizedlist,
             }
             
    def __call__(self, nbxml):
        r = nbxml.getroot()
        if r.get('version') != '1':
            raise ValueError('need notebook with version="1"')
        newr = ET.Element(ip.notebook, nsmap=nsmap(ip, db), version='1.1')
        for elem in r:
            newr.append(elem)
        for elem in newr.getiterator():
            newtag = self.tagmap.get(elem.tag, elem.tag)
            elem.tag = newtag
        return ET.ElementTree(newr)

def get_converters():
    cvrt = {}
    c = Convert1to1_1()
    cvrt[c.fromto] = c
    return cvrt

if __name__ == '__main__':
    import sys
    import os
    import optparse
    from notabene.notebook import Notebook

    parser = optparse.OptionParser()
    parser.add_option('-n', '--no-backup', dest='backup', action='store_false',
        default=True, help="don't backup converted file to filename.pybk.orig")
    parser.add_option('-t', '--to-version', dest='to_version', action='store',
        default='1.1', help="version to convert to")
    options, args = parser.parse_args()

    cvrts = get_converters()
    for fn in args:
        nbxml = ET.parse(fn)
        fromto = (nbxml.getroot().get('version'), options.to_version)
        if fromto not in cvrts:
            print 'Do not have a converter from %s to %s' % fromto
            raise SystemExit
        converter = cvrts[fromto]
        nbxml2 = converter(nbxml)
        if options.backup:
            os.rename(fn, fn+'.orig')
        nbxml2.write(fn)