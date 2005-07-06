"""
Class which mimics a module.

Needed to allow pickle to correctly resolve namespaces during IPython
sessions.

$Id$
"""

class FakeModule:
    """Simple class with attribute access to fake a module.

    This is not meant to replace a module, but to allow inserting a fake
    module in sys.modules so that systems which rely on run-time module
    importing (like shelve and pickle) work correctly in interactive IPython
    sections.

    Do NOT use this code for anything other than this IPython private hack."""

    def __init__(self,adict):
        self.__dict__ = adict

    def __getattr__(self,key):
        return self.__dict__[key]

