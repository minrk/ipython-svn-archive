# -*- coding: iso-8859-1 -*-
"""
Pdb debugger class.

Modified from the standard pdb.Pdb class to avoid including readline, so that
the command line completion of other programs which include this isn't
damaged.

In the future, this class will be expanded with improvements over the standard
pdb.

The code in this file is mainly lifted out of cmd.py in Python 2.2, with minor
changes. Licensing should therefore be under the standard Python terms.

$Id$"""

import Release
__version__ = Release.version
__date__    = Release.date
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = 'Python'

import pdb,bdb,cmd,os,sys

# Workaround for lack of 'completekey' keyword in 2.1's version of cmd.Cmd
if sys.version[0:3] < '2.2':
    class Command(cmd.Cmd):
        def __init__(self, completekey=None):
            pass
else:
    Command = cmd.Cmd


class Pdb(pdb.Pdb, bdb.Bdb, Command):
    """Modified Pdb class, does not load readline."""
    def __init__(self):
        bdb.Bdb.__init__(self)
        Command.__init__(self,completekey=None) # don't load readline
        self.prompt = '(Pdb) '
        self.aliases = {}

        # Read $HOME/.pdbrc and ./.pdbrc
        self.rcLines = []
        if os.environ.has_key('HOME'):
            envHome = os.environ['HOME']
            try:
                rcFile = open(os.path.join(envHome, ".pdbrc"))
            except IOError:
                pass
            else:
                for line in rcFile.readlines():
                    self.rcLines.append(line)
                rcFile.close()
        try:
            rcFile = open(".pdbrc")
        except IOError:
            pass
        else:
            for line in rcFile.readlines():
                self.rcLines.append(line)
            rcFile.close()
