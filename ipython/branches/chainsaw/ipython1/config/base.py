#!/usr/bin/env python
# encoding: utf-8
"""
Configuration objects for IPython's configuration and customization.

See the docstrings of ConfigData and ConfigurationBase for more details.
"""
#*****************************************************************************
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import os
import sys

from IPython.genutils import get_home_dir

ipython_path = get_home_dir() + '/.ipython'

class ConfigData(object):
    """A class that contains configuration data.
    
    The Config data class is designed to be a simple bag for configuration
    related data.  Eventually this class will be based on enthought.traits to
    allow for validation of config data, but for now it is a simple class.
    
    Instances of this class are created as the data attribute of ConfigurationBase 
    instances and should be accessed through that route.
    """
    def __setattr__(self, name, value):
        """This should print data as it is assigned, but it doesn't always."""
        print "Setting %s to: " % name, repr(value)
        self.__dict__[name] = value

class ConfigurationBase(object):
    """A class to manage configuration data.
    
    This class creates an attribute, data that points to a ConfigData instance.
    This attribute contains all the config data for a specific subsystem of IPython.
    The various methods of this class are meant to provide means of updating the
    data from files or dictionaries.
    
    Class Methods:
    - configFiles: a list of file names from which to load config data
    - configDataClass: a subclass of ConfigData
    """
    
    configFiles = ['ipython1rc.py']
    configDataClass = ConfigData
    
    def __init__(self):
        self.data = self.configDataClass()        
        
    def updateWithConfigFiles(self):
        """Update the config data using the configFiles.
        
        The files named in configFiles are read for config data related to this
        class.  This happens by executing the contents of the config file in
        a namespace with one attribute defined: the name of this class.  Thus if
        a class FooConfig is being configured, the config file should contain lines
        like:
        
        FooConfig.bar = 'this is the bar string'
        
        Thus, the bar attribute of FooConfig's data container will be updated.
        """
        configFilePaths = [self._resolveFilePath(f) for f in self.configFiles]
        for cf in configFilePaths:
            if cf is not None:
                print "Loading configuration from: " + cf
                dataNamespace = {self.__class__.__name__: self.configDataClass}
                execfile(cf, dataNamespace)
     
    def _resolveFilePath(self, filename):
        """Resolve filenames into paths.
        
        This looks in the following order:
        
        1.  In the current working directory
        2.  In the ~/.ipython directory
        3.  By absolute path resolving the ~
        """
        resolvedFile = None
        if os.path.isfile(filename):
            return filename
        tryPath = get_home_dir() + '/.ipython/' + filename
        if os.path.isfile(tryPath):
            resolvedFile = tryPath
        elif os.path.isfile(os.path.expanduser(filename)):
            resolvedFile = os.path.expanduser(filename)
        return resolvedFile
        
    def update(self, **kwargs):
        for k, v in kwargs.iteritems():
            if hasattr(self.data, k):
                print "Setting %s to: " % k + repr(v)
                setattr(self.data, k, v)



