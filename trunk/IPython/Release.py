# -*- coding: iso-8859-1 -*-
"""Release data for the IPython project."""

# $Id$

name = 'IPython'

version = '0.5.0.rc2cvs'

description = "An enhanced interactive Python shell."

long_description = \
"""
IPython provides a replacement for the interactive Python interpreter with
extra functionality.

Main features:

 * Comprehensive object introspection.

 * Input history, persistent across sessions.

 * Caching of output results during a session with automatically generated
   references.

 * Readline based name completion.

 * Extensible system of 'magic' commands for controlling the environment and
   performing many tasks related either to IPython or the operating system.

 * Configuration system with easy switching between different setups (simpler
   than changing $PYTHONSTARTUP environment variables every time).

 * Session logging and reloading.

 * Extensible syntax processing for special purpose situations.

 * Access to the system shell with user-extensible alias system.

 * Easily embeddable in other Python programs.

 * Integrated access to the pdb debugger and the Python profiler. """

license = 'LGPL'

authors = {'Fernando' : ('Fernando Perez','fperez@colorado.edu'),
           'Janko' : ('Janko Hauser','jh@comunit.de'),
           'Nathan' : ('Nathaniel Gray','n8gray@caltech.edu')
           }

url = 'http://ipython.scipy.org'

platforms = ['Linux','Mac OSX','Windows XP/2000/NT','Windows 95/98/ME']

keywords = ['Interactive','Interpreter','Shell']

# Get date dynamically
import time
date = time.asctime()
del time
