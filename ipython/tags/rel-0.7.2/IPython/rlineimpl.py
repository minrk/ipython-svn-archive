# -*- coding: utf-8 -*-
""" Imports and provides the "correct" version of readline for the platform.

Readline is used throughout IPython as "import IPython.rlineimpl as readline.

In addition to normal readline stuff, this module provides have_readline boolean 
and _outputfile variable used in genutils.

$Id: Magic.py 1096 2006-01-28 20:08:02Z vivainio $"""


import sys

have_readline = False

if sys.platform == 'win32':
    try:
        import pyreadline.rlmain
        #add config for inputrcpath here:
        #pyreadline.rlmain.config_path="c:/python/test_config.ini"
        from readline import *
        #print "Using the new pyreadline (thanks for participating in the testing!)"
        
        have_readline = True
        
        import readline as _rl
    except ImportError:
        #print "IPython team recommends the new pyreadline for Windows use, "
        #print "It's superior especially with non-US keyboard layouts."
        #print "Try installing it with 'easy_install pyreadline (ctypes is required) or"
        #print "svn co http://ipython.scipy.org/svn/ipython/pyreadline/trunk pyreadline"
        #print "Trying 'old' windows readline."
        #print "Using 'old' readline, you might want to try pyreadline:"
        #print "http://projects.scipy.org/ipython/ipython/wiki/PyReadline/Intro"
        try:
            from readline import *
            import readline as _rl
            have_readline = True
        except ImportError:
            pass

    if have_readline:
        try:
            _outputfile=_rl.GetOutputFile()
        except NameError:
            print "Failed GetOutputFile"
            have_readline = False
    
else:
    try:
        from readline import *
        have_readline = True
    except ImportError:
        pass
