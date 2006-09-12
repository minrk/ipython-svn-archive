#!/usr/bin/env python
# encoding: utf-8
"""
ipenginerc.py
"""

# Get a valid configuration object for the engine and shell

from ipython1.config.api import getConfigObject 

enginerc = getConfigObject('engine')
shellrc = getConfigObject('shell')

# Now we can configure the engine and shell

enginerc.mpiImportStatement = 'from ipython1.kernel import mpi'