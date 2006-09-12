#!/usr/bin/env python
# encoding: utf-8
"""
shellrc.py
"""

# Get a valid configuration object for the shell

from ipython1.config.api import getConfigObject

shellrc = getConfigObject('shell')

# Now we can configure the shell

from ipython1.core.shell import InteractiveShell

shellrc.shellClass = InteractiveShell
shellrc.filesToRun = []

