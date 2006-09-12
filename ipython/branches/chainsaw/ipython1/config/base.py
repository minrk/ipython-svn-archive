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
        
class Config(object):
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

class ConfigHelper(object):
    """A class to manage configuration data.
    
    This class creates an attribute, data that points to a ConfigData instance.
    This attribute contains all the config data for a specific subsystem of IPython.
    The various methods of this class are meant to provide means of updating the
    data from files or dictionaries.
    
    Class Methods:
    - configFiles: a list of file names from which to load config data
    - configDataClass: a subclass of ConfigData
    """

    configClass = Config
    
    def __init__(self):
        self.data = self.configClass()        
        
    def update(self, **kwargs):
        for k, v in kwargs.iteritems():
            if hasattr(self.data, k):
                print "Setting %s to: " % k + repr(v)
                setattr(self.data, k, v)

