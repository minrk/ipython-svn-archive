# encoding: utf-8
"""
This is the official entry point to IPython's configuration system.  

There are two ways this module can be used:

1.  To customize various components of IPython.
2.  To access to configuration information for various components of IPython.

Customization
=============

Configuration information is held by a set of configuration objects.  The
attributes of these objects contain the actual configuration information.  A
user performs customization by getting one of the configuration objects:

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

The actual configuration information about something can be retrieved in a
similar manner:

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
__docformat__ = "restructuredtext en"
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelley <benjaminrk@gmail.com>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

import os
from ipython1.config.cutils import getHomeDir, getIpythonDir
from ipython1.external.configobj import ConfigObj

class ConfigObjManager(object):
    
    def __init__(self, configObj, filename=None):
        self.current = configObj
        self.filename = filename
        
    def getConfigObj(self):
        return self.current
    
    def updateConfigObj(self, newConfig):
        self.current.merge(newConfig)
        
    def updateConfigObjFromFile(self, filename):
        newConfig = ConfigObj(filename, file_error=False)
        self.current.merge(newConfig)
        
    def updateConfigObjFromDefaultFile(self, ipythondir=None):
        if self.filename is not None:
            fname = self.resolveFilePath(self.filename, ipythondir)
            print fname
            self.updateConfigObjFromFile(fname)

    def writeConfigObjToFile(self, filename):
        f = open(filename, 'w')
        self.current.write(f)
        f.close()

    def asImportable(self, key):
        package = '.'.join(key.split('.')[0:-1])
        obj = key.split('.')[-1]
        execString = 'from %s import %s' % (package, obj)
        exec execString
        exec 'temp = %s' % obj 
        print temp
        return temp  

    def resolveFilePath(self, filename, ipythondir = None):
        """Resolve filenames into absolute paths.

        This function looks in the following directories in order:

        1.  In the current working directory or by absolute path with ~ expanded
        2.  In ipythondir if that is set
        3.  In the IPYTHONDIR environment variable if it exists
        4.  In the ~/.ipython directory

        Note: The IPYTHONDIR is also used by the trunk version of IPython so
               changing it will also affect it was well.
        """

        # In cwd or by absolute path with ~ expanded
        trythis = os.path.expanduser(filename)
        if os.path.isfile(trythis):
            return trythis

        # In ipythondir if it is set
        if ipythondir is not None:
            trythis = ipythondir + '/' + filename
            if os.path.isfile(trythis):
                return trythis        

        # In the IPYTHONDIR environment variable if it exists
        IPYTHONDIR = os.environ.get('IPYTHONDIR')
        if IPYTHONDIR is not None:
            trythis = IPYTHONDIR + '/' + filename
            if os.path.isfile(trythis):
                return trythis

        # In the ~/.ipython directory
        trythis = getHomeDir() + '/.ipython/' + filename
        if os.path.isfile(trythis):
            return trythis

        return None


    
    

    
