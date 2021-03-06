# -*- coding: utf-8 -*-
"""
Class which mimics a module.

Needed to allow pickle to correctly resolve namespaces during IPython
sessions.

$Id$"""

#*****************************************************************************
#       Copyright (C) 2002-2004 Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

class FakeModule:
    """Simple class with attribute access to fake a module.

    This is not meant to replace a module, but to allow inserting a fake
    module in sys.modules so that systems which rely on run-time module
    importing (like shelve and pickle) work correctly in interactive IPython
    sessions.

    Do NOT use this code for anything other than this IPython private hack."""

    def __init__(self,adict):

        # It seems pydoc (and perhaps others) needs any module instance to
        # implement a __nonzero__ method, so we add it if missing:
        if '__nonzero__' not in adict:
            def __nonzero__():
                return 1
            adict['__nonzero__'] = __nonzero__

            self.__dict__ = adict

    def __getattr__(self,key):
        try:
            return self.__dict__[key]
        except KeyError, e:
            raise AttributeError("FakeModule object has no attribute %s" % e)

    def __str__(self):
        return "<IPython.FakeModule instance>"

    def __repr__(self):
        return str(self)
