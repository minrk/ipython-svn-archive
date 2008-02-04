import sys, os
from textwrap import fill

display_status=True

if display_status:
    def print_line(char='='):
        print char * 76

    def print_status(package, status):
        initial_indent = "%22s: " % package
        indent = ' ' * 24
        print fill(str(status), width=76,
                   initial_indent=initial_indent,
                   subsequent_indent=indent)

    def print_message(message):
        indent = ' ' * 24 + "* "
        print fill(str(message), width=76,
                   initial_indent=indent,
                   subsequent_indent=indent)

    def print_raw(section):
        print section
else:
    def print_line(*args, **kwargs):
        pass
    print_status = print_message = print_raw = print_line

def check_for_ipython():
    try:
        import IPython
    except ImportError:
        print_status("IPython", "Not found, aborting")
        return False
    else:
        print_status("IPython", IPython.__version__)
        return True

def check_for_zopeinterface():
    try:
        import zope.interface
    except ImportError:
        print_status("zope.Interface", "Not found, aborting")
        return False
    else:
        print_status("Zope.Interface","yes")
        return True
        
def check_for_twisted():
    try:
        import twisted
    except ImportError:
        print_status("Twisted", "Not found, aborting")
        return False
    else:
        major = twisted.version.major
        minor = twisted.version.minor
        micro = twisted.version.micro
        if not (major==2 and minor==5 and micro==0):
            print_message("WARNING: IPython1 requires Twisted 2.5.0, you have version %s, aborting"%twisted.version.short())
            return False
        else:
            print_status("Twisted", twisted.version.short())
            return True

def check_for_pexpect():
    try:
        import pexpect
    except ImportError:
        print_status("pexpect", "no (required for running standalone doctests)")
        return False
    else:
        print_status("pexpect","yes")
        return True

def check_for_httplib2():
    try:
        import httplib2
    except ImportError:
        print_status("httplib2", "no (required for blocking http clients)")
        return False
    else:
        print_status("httplib2","yes")
        return True

def check_for_sqlalchemy():
    try:
        import sqlalchemy
    except ImportError:
        print_status("sqlalchemy", "no (required for the ipython1 notebook)")
        return False
    else:
        print_status("sqlalchemy","yes")
        return True

def check_for_simplejson():
    try:
        import simplejson
    except ImportError:
        print_status("simplejson", "no (required for the ipython1 notebook)")
        return False
    else:
        print_status("simplejson","yes")
        return True

        