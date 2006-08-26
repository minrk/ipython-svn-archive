#!/usr/bin/env python
# encoding: utf-8
"""
Utilities to load configuration into Configuration objects.
"""

import sys, os
from IPython.genutils import get_home_dir

ipython_path = get_home_dir() + '/.ipython'

def configure(configObject):
    """Take a instance of a Configuration object and update it using config files."""
    configFiles = configObject.configFiles
    configFiles = [resolveFilePath(f) for f in configFiles]
    for cf in configFiles:
        if cf is not None:
            print "Loading configuration from: " + cf
            f = open(cf, 'r')
            fileContents = f.read()
            f.close()
            definedAttributes = {}
            exec fileContents in definedAttributes
            configObject.update(**definedAttributes)
        else:
            print "could not load config file"
            
def resolveFilePath(filename):
    resolvedFile = None
    if os.path.isfile(filename):
        return filename
    tryPath = get_home_dir() + '/.ipython/' + filename
    if os.path.isfile(tryPath):
        resolvedFile = tryPath
    elif os.path.isfile(os.path.expanduser(filename)):
        resolvedFile = os.path.expanduser(filename)
    return resolvedFile
            
        
        
    
