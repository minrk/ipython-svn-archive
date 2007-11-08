# encoding: utf-8
"""
This is the official entry point to IPython's configuration system.  
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
    
    def __init__(self, configObj, filename):
        self.current = configObj
        self.current.indent_type = '    '
        self.filename = filename
        # Don't write the default config file unless needed!
        #self.writeDefaultConfigFile()
        
    def getConfigObj(self):
        return self.current
    
    def updateConfigObj(self, newConfig):
        self.current.merge(newConfig)
        
    def updateConfigObjFromFile(self, filename):
        newConfig = ConfigObj(filename, file_error=False)
        self.current.merge(newConfig)
        
    def updateConfigObjFromDefaultFile(self, ipythondir=None):
        fname = self.resolveFilePath(self.filename, ipythondir)
        self.updateConfigObjFromFile(fname)

    def writeConfigObjToFile(self, filename):
        f = open(filename, 'w')
        self.current.write(f)
        f.close()

    def writeDefaultConfigFile(self):
        ipdir = getIpythonDir()
        fname = ipdir + '/' + self.filename
        if not os.path.isfile(fname):
            print "Writing the configuration file to: " + fname
            self.writeConfigObjToFile(fname)
    
    def _import(self, key):
        package = '.'.join(key.split('.')[0:-1])
        obj = key.split('.')[-1]
        execString = 'from %s import %s' % (package, obj)
        exec execString
        exec 'temp = %s' % obj 
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

        trythis = getIpythonDir() + '/' + filename
        if os.path.isfile(trythis):
            return trythis

        return None


    
    

    
