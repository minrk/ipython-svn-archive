"""Little utilities for testing tconfig.

This module is meant to be used via

import tctst; reload(tctst)
from tctst import *

at the top of the actual test scripts, so that they all get the entire set of
common test tools with minimal fuss.
"""

# Standard library imports
import os
import sys
from pprint import pprint

# Our own imports.

import tconfig
reload(tconfig)

from tconfig import mkConfigObj, RecursiveConfigObj, RecursiveConfigManager, \
     tconf2File

# Simple utilities/classes for testing

def cat(fname):
    print '### FILENAME:',fname
    print open(fname).read()


class App(object):
    """A trivial 'application' class to be initialized.
    """
    def __init__(self,configClass,configFilename):
        self.rcman = RecursiveConfigManager(configClass,configFilename)
        self.rc = self.rcman.tconf
