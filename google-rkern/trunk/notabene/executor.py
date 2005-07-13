import code
import sys
import itertools
import pprint

from IPython import OutputTrap, ultraTB
from lxml import etree as ET

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
        inputs = oldlog.xpath('./input')
        for inp in inputs:
            number = inp.get('number')
            newinp = ET.SubElement(newlog, 'input', number=number)
            newinp.text = inp.text
            retdict = self.run_one(inp.text)
            if retdict is not None:
                for tag, value in retdict.iteritems():
                    elem = ET.SubElement(newlog, tag, number=number)
                    elem.text = value
        self.rm_hooks()

    def rerun_since(self, log, number):
        """Rerun all inputs >= number and append them to the log.
        """
        self.add_hooks()
        inputs = oldlog.xpath('./input[@number>=%s]' % number)
        curnum = int(inputs[-1].get('number'))
        for inp in inputs:
            curnum += 1
            newinp = ET.SubElement(log, 'input', number=str(curnum))
            newinp.text = inp.text
            retdict = self.run_one(inp.text)
            if retdict is not None:
                for tag, value in retdict.iteritems():
                    elem = ET.SubElement(log, tag, number=str(curnum))
                    elem.text = value
        self.rm_hooks()

    def vacuum(self, sheet, root=None):
        """Remove all unreferenced cells from logs.

        XXX: And if we have multiple sheets? This is almost certainly the wrong
        way to do this.
        """
        # get all unique logids from the relevant elements in the sheet
        logids = set(sheet.xpath('.//@logid'))
        if root is None:
            root = sheet.xpath('/')[0]
        for logid in logids:
            # get the log; this assumes
            log = root.xpath('/ipython-log[@id="%s"]' % logid)[0]
            # get all ipython-cell elements from ipython-blocks with this logid
            cells = sheet.xpath('./ipython-block[@logid="%s"]/ipython-cell' %
                logid)
            # get all ipython-figure elements with this logid
            figs = sheet.xpath('./ipython-figure[@logid="%s"]' % logid)
            keepers = set((x.get('type'), x.get('number')) for x in cells)
            keepers.update(('figure', x.get('number')) for x in figs)
            items = list(log)
            for elem in items:
                if (elem.tag, elem.get('number')) not in keepers:
                    log.remove(elem)

    def contiguify(self, log, sheets=None):
        """Renumber cells in a log to make them contiguous.

        If sheets are provided, renumber the appropriate elements, too.
        """
        numbers = sorted(set(int(x) for x in log.xpath('.//@number')))
        old2new = {}
        for i, oldnum in enumerate(numbers):
            newnum = str(i + 1)
            old2new[oldnum] = newnum
            for elem in log.xpath('.//[@number="%s"]' % oldnum):
                elem.set('number', newnum)

        logid = log.get('id')
        if sheets is not None:
            for sheet in sheets:
                cells = sheet.xpath('.//ipython-block[@logid="%s"]//' % logid)
                figs = sheet.xpath('.//ipython-figure[@logid="%s"]' % logid)
                elems = cells + figs
                for x in elem:
                    x.set('number', old2new.get(x.get('number')))



