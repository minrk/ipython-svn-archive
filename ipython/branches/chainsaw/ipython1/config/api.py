#!/usr/bin/env python
# encoding: utf-8
"""
This is the official entry point to IPython's configuration system.  

There are two ways this module can be used:

1.  To customize various components of IPython.
2.  To access to configuration information for various components of IPython.

Customization
=============

Configuration information is held by a set of configuration objects.  The attributes
of these objects contain the actual configuration information.  A user performs
customization by getting one of the configuration objects:

::

    import ipython1.config.api as config
    enginerc = config.getConfigObject('engine')
    
And then setting attributes of that object:

::

    enginerc.maxMessageSize = 100
    
Documentation on the types of configuration objects and the meaning of their
attributes can be found in the ipython1.config.objects module.

Access to Configuration Information
===================================

The actual configuration information about something can be retrieved in a similar 
manner:

::

    import ipython1.config.api as config
    enginerc = config.getConfigObject('engine')
    maxMessageSize = enginerc.maxMessageSize

Questions about the sysetem
===========================

1.  How should we allow IPYTHONDIR to be set as a command line option?
2.  Should we distinguish between profiles and configuration files?
3.  How should we enforce dependencies?

"""

import os
from IPython.genutils import get_home_dir
from ipython1.config.objects import configHelperClasses

_configObjects = {}

def getConfigObject(key):
    """Return a new or previously created configuration object by key.
    
    Configuration objects for a given key are created only once for each process.
    Thus configurationi objects needs to be created/configured only once per process.

    This function returns a configuration object either by creating a new one or by
    finding an already existing one in the cache.
    """
    
    global _configObjects
    global configHelperClasses
    co = _configObjects.get(key)
    if co is None:
        klass = configHelperClasses[key]
        _configObjects[key] = klass()
    return _configObjects[key].data
        

def getConfigHelperObject(key):
    """Return a new or previously created configuration helper object by key.
    
    This function works the same way as getConfigObject, but it returns the 
    configuration helper object rather than its data attribute.
    """
    
    global _configObjects
    global configHelperClasses
    co = _configObjects.get(key)
    if co is None:
        klass = configHelperClasses[key]
        _configObjects[key] = klass()
    return _configObjects[key]


def updateConfigWithFile(filename, ipythondir = None):
    """Update all configuration objects from a config file."""
    f = resolveFilePath(filename, ipythondir)
    if f is not None:
        execfile(f)
    
def resolveFilePath(filename, ipythondir = None):
    """Resolve filenames into absolute paths.
    
    This function looks in the following directories in order:
    
    1.  In the current working directory or by absolute path with ~ expanded
    2.  In ipythondir if that is set
    3.  In the IPYTHONDIR environment variable if it exists
    4.  In the ~/.ipython directory

    Note:  The IPYTHONDIR is also used by the trunk version of IPython so changing 
           it will also affect it was well.
    """
    
    # In cwd or by absolute path with ~ expanded
    firstTry = os.path.expanduser(filename)
    if os.path.isfile(firstTry):
        return firstTry
        
    # In ipythondir if it is set
    if ipythondir:
        secondTry = ipythondir + '/' + filename
        if os.path.isfile(secondTry):
            return secondTry        
        
    # In the IPYTHONDIR environment variable if it exists
    IPYTHONDIR = os.environ.get('IPYTHONDIR')
    if IPYTHONDIR is not None:
        thirdTry = IPYTHONDIR + '/' + filename
        if os.path.isfile(thirdTry):
            return thirdTry
        
    # In the ~/.ipython directory
    forthTry = get_home_dir() + '/.ipython/' + filename
    if os.path.isfile(forthTry):
        return forthTry
        
    return None

def updateConfigWithProfile(base, name, ipythondir = None):
    """Updates all configuration objects using a profile.
    
    The full profile name is built as baserc_name.py."""
    f = resolveProfile(base, name, ipythondir)
    if f is not None:
        execfile(f)

def resolveProfile(base, name, ipythondir = None):
    """Builds a full profile name baserc_name.py and resolves its path."""
    fullProfileName = base + 'rc_' + name + '.py'
    return resolveFilePath(fullProfileName, ipythondir)
    
    

    