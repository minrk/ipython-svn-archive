from notabene import executor
import sys

def setup_module(module):
    module.old_excepthook = sys.excepthook
    module.old_displayhook = sys.displayhook

def teardown_module(module):
    sys.excepthook = module.old_excepthook
    sys.displayhook = module.old_displayhook

class TestExecutor(object):
    def setup_class(cls):
        cls.exc = executor.Executor()

    def test_add_rm_hooks(self):
        self.exc.add_hooks()
        self.exc.rm_hooks()
        assert old_excepthook == sys.excepthook
        assert old_displayhook == sys.displayhook

    def setup_method(self, method):
        if method.__name__.startswith('test_run_one_'):
            self.exc.add_hooks()

    def teardown_method(self, method):
        if method.__name__.startswith('test_run_one_'):
            self.exc.rm_hooks()

    def test_run_one_simple(self):
        rd = self.exc.run_one('1')
        assert self.exc.last_repr is None
        assert rd['output'] == '1'
        assert 'traceback' not in rd
        assert 'stdout' not in rd
        assert 'stderr' not in rd

    def test_run_one_import(self):
        rd = self.exc.run_one('import sys')
        assert self.exc.last_repr is None
        assert 'output' not in rd
        assert 'traceback' not in rd
        assert 'stdout' not in rd
        assert 'stderr' not in rd
        assert 'sys' in self.exc.namespace

    def test_run_one_stdout(self):
        rd = self.exc.run_one('sys.stdout.write("foo")')
        assert self.exc.last_repr is None
        assert 'output' not in rd
        assert 'traceback' not in rd
        assert rd['stdout'] == 'foo'
        assert 'stderr' not in rd

    def test_run_one_stderr(self):
        rd = self.exc.run_one('sys.stderr.write("foo")')
        assert self.exc.last_repr is None
        assert 'output' not in rd
        assert 'traceback' not in rd
        assert 'stdout' not in rd
        assert rd['stderr'] == 'foo'

    def test_run_one_traceback(self):
        rd = self.exc.run_one('1 / 0')
        assert self.exc.last_repr is None
        assert 'output' not in rd
        assert 'traceback' in rd
        assert 'stdout' not in rd
        assert 'stderr' not in rd

    def test_run_one_syntaxerror(self):
        rd = self.exc.run_one('$!][')
        assert self.exc.last_repr is None
        assert 'output' not in rd
        assert 'traceback' in rd
        assert 'stdout' not in rd
        assert 'stderr' not in rd

    def test_run_one_continue(self):
        rd = self.exc.run_one('def foo(x):')
        assert rd is None

