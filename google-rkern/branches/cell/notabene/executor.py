import code
import sys
import itertools
import pprint

from IPython import OutputTrap, ultraTB
from lxml import etree as ET

from notabene import notebook

class Executor(object):
    def __init__(self, namespace=None):
        if namespace is None:
            namespace = {}
        self.namespace = namespace

        self.last_repr = None
        self.excepthook = ultraTB.FormattedTB(mode='Verbose',
            color_scheme='NoColor')

    def add_hooks(self):
        self.old_displayhook = sys.displayhook
        sys.displayhook = self.displayhook
        ##self.old_excepthook = sys.excepthook
        ##sys.excepthook = self.excepthook
    
    def rm_hooks(self):
        sys.displayhook = self.old_displayhook
        ##sys.excepthook = self.old_excepthook

    def displayhook(self, obj):
        self.last_repr = pprint.pformat(obj)

    def run_one(self, input):
        """Run one input and collect all forms of output.
        """
        retdict = {}
        try:
            ret = code.compile_command(input)
        except (SyntaxError, OverflowError, ValueError):
            etype, value, tb = sys.exc_info()
            retdict['traceback'] = self.excepthook.text(etype, value, tb)
            return retdict
        if ret is None:
            return None
        trap = OutputTrap.OutputTrap()
        try:
            trap.trap_all()
            exec ret in self.namespace
            trap.release_all()
        except:
            etype, value, tb = sys.exc_info()
            retdict['traceback'] = self.excepthook.text(etype, value, tb)
            return retdict

        if self.last_repr is not None:
            retdict['output'] = self.last_repr
            self.last_repr = None
        stdout = trap.out.getvalue()
        if stdout:
            retdict['stdout'] = stdout
        stderr = trap.err.getvalue()
        if stderr:
            retdict['stderr'] = stderr

        return retdict

    def run_all(self, oldlog, newlog):
        """Run all inputs from oldlog to create newlog.
        """
        self.add_hooks()
        cells = sorted((Cell(x) for x in oldlog), key=lambda x: x.number)
        for cell in cells:
            newcell = ET.SubElement(newlog, 'cell', number=str(cell.number))
            input = ET.SubElement(newcell, 'input')
            input.text = cell.input
            retdict = self.run_one(cell.input)
            if retdict is not None:
                for tag, value in retdict.iteritems():
                    elem = ET.SubElement(newcell, tag)
                    elem.text = value
        self.rm_hooks()

    def rerun_since(self, log, number):
        """Rerun all inputs >= number and append them to the log.
        """
        self.add_hooks()
        cells = sorted((Cell(x) for x in
            oldlog.xpath('./cell[@number>=%s]' % number)),
            key=lambda x: x.number)
        curnum = cells[-1].number
        for cell in cells:
            curnum += 1
            newcell = ET.SubElement(log, 'cell', number=str(curnum))
            input = ET.SubElement(newcell, 'input')
            input.text = cell.input
            retdict = self.run_one(input.text)
            if retdict is not None:
                for tag, value in retdict.iteritems():
                    elem = ET.SubElement(newcell, tag)
                    elem.text = value
        self.rm_hooks()

    def vacuum(self, nb):
        """Remove all unreferenced cells from logs.
        """
        sheets = nb.root.xpath('./sheet')
        keepers = {}
        for sheet in sheets:
            # get all unique logids from the relevant elements in the sheet
            logids = set(sheet.xpath('.//@logid'))
            for logid in logids:
                # get the log
                log = nb.get_log(logid)
                # get all ipython-cell elements from ipython-blocks with this logid
                cells = sheet.xpath('.//ipython-block[@logid="%s"]/ipython-cell' %
                    logid)
                # get all ipython-figure elements with this logid
                figs = sheet.xpath('.//ipython-figure[@logid="%s"]' % logid)
                logkeepers = keepers.get(logid, set())
                logkeepers.update((x.get('type'), x.get('number')) for x in cells)
                logkeepers.update(('figure', x.get('number')) for x in figs)
                keepers[logid] = logkeepers
        for logid in logids:
            log = nb.get_log(logid)
            logkeepers = keepers[logid]
            cells = list(log)
            for cell in cells:
                num = cell.get('number')
                for subcell in list(cell):
                    if (subcell.tag, num) not in logkeepers:
                        cell.remove(subcell)
                if len(cell) == 0:
                    log.remove(cell)

    def contiguify(self, log, sheets=None):
        """Renumber cells in a log to make them contiguous.

        If sheets are provided, renumber the appropriate elements, too.
        """
        numbers = sorted(int(x) for x in log.xpath('./cell/@number'))
        old2new = {}
        for i, oldnum in enumerate(numbers):
            newnum = str(i + 1)
            old2new[oldnum] = newnum
            for elem in log.xpath('.//[@number="%s"]' % oldnum):
                elem.set('number', newnum)

        if sheets is not None:
            logid = log.get('id')
            for sheet in sheets:
                cells = sheet.xpath('.//ipython-block[@logid="%s"]//' % logid)
                figs = sheet.xpath('.//ipython-figure[@logid="%s"]' % logid)
                elems = cells + figs
                for x in elem:
                    x.set('number', old2new.get(x.get('number')))



