import code
import sys

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
        retdict = {}
        try:
            ret = code.compile_command(input)
        except (SyntaxError, OverflowError, ValueError):
            etype, value, tb = sys.exc_info()
            retdict['traceback'] = self.excepthook.text(etype, value, tb)
            return retdict
        if ret is None:
            return None
        trap = OutputTrap()
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
        self.add_hooks()
        inputs = oldlog.xpath('./input')
        for inp in inputs:
            number = inp.get('number')
            retdict = self.run_one(inp.text)
            if retdict is not None:
                for tag, value in retdict.iteritems():
                    elem = ET.SubElement(tag, number=number)
                    elem.text = value
        self.rm_hooks()

