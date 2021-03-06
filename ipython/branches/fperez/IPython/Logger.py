"""
Logger class for IPython's logging facilities.
"""

from __future__ import nested_scopes

#*****************************************************************************
#       Copyright (C) 2001 Janko Hauser <jhauser@ifm.uni-kiel.de> and
#                          Fernando P�rez <fperez@pizero.colorado.edu>
#
#  Distributed under the terms of the GNU Lesser General Public License (LGPL)
#
#    This code is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#  The full text of the LGPL is available at:
#
#                  http://www.gnu.org/copyleft/lesser.html
#*****************************************************************************

#****************************************************************************
# Modules and globals

import Release
__version__ = Release.version
__date__    = Release.date
__author__  = '%s <%s>\n%s <%s>' % \
              ( Release.authors['Janko'] + Release.authors['Fernando'] )
__license__ = Release.license

# Python standard modules
import os, sys,glob

# Homebrewed
from genutils import *


#****************************************************************************
# FIXME: The logger class shouldn't be a mixin, it throws too many things into
# the InteractiveShell namespace. Rather make it a standalone tool, and create
# a Logger instance in InteractiveShell that uses it. Doing this will require
# tracking down a *lot* of nasty uses of the Logger attributes in
# InteractiveShell, but will clean up things quite a bit.

class Logger:
    """A Logfile Mixin class with different policies for file creation"""

    # FIXME: once this isn't a mixin, log_ns should just be 'namespace', since the
    # names won't collide anymore.
    def __init__(self,log_ns):
        self._i00,self._i,self._ii,self._iii = '','','',''
        self.do_full_cache = 0 # FIXME. There's also a do_full.. in OutputCache
        self.log_ns = log_ns
        # defaults
        self.LOGMODE = 'backup'
        self.defname = 'logfile'
        
    def create_log(self,header='',fname='',defname='.Logger.log'):
        """Generate a new log-file with a default header"""
        if fname:
            self.LOG = fname

        if self.LOG:
            self.logfname = self.LOG
        else:
            self.logfname = defname
        
        if self.LOGMODE == 'over':
            if os.path.isfile(self.logfname):
                os.remove(self.logfname) 
            self.logfile = open(self.logfname,'w')
        if self.LOGMODE == 'backup':
            if os.path.isfile(self.logfname):
                os.rename(self.logfname,self.logfname+'~')
            self.logfile = open(self.logfname,'w')
        elif self.LOGMODE == 'global':
            self.logfname = os.path.join(self.home_dir, self.defname)
            self.logfile = open(self.logfname, 'a')
            self.LOG = self.logfname
        elif self.LOGMODE == 'rotate':
            if os.path.isfile(self.logfname):
                if os.path.isfile(self.logfname+'.1~'): 
                    old = glob.glob(self.logfname+'.*~')
                    old.reverse()
                    for f in old:
                        root, ext = os.path.splitext(f)
                        num = int(ext[1:-1])+1
                        os.rename(f, root+'.'+`num`+'~')
                os.rename(self.logfname, self.logfname+'.1~')
            self.logfile = open(self.logfname,'w')
        elif self.LOGMODE == 'append':
            self.logfile = open(self.logfname,'a')
            
        if self.LOGMODE != 'append':
            self.logfile.write(header)
        self.logfile.flush()

    def logstart(self, header='',parameter_s = ''):
        if not hasattr(self, 'LOG'):
            logfname = self.LOG or parameter_s or './'+self.defname
            self.create_log(header,logfname)
        elif parameter_s and hasattr(self,'logfname') and \
             parameter_s != self.logfname:
            self.close_log()
            self.create_log(header,parameter_s)
            
        self._dolog = 1

    def switch_log(self,val):
        """Switch logging on/off. val should be ONLY 0 or 1."""

        if not val in [0,1]:
            raise ValueError, \
                  'Call switch_log ONLY with 0 or 1 as argument, not with:',val
        
        label = {0:'OFF',1:'ON'}

        try:
            _ = self.logfile
        except AttributeError:
            print """
Logging hasn't been started yet (use @logstart for that).

@logon/@logoff are for temporarily starting and stopping logging for a logfile
which already exists. But you must first start the logging process with
@logstart (optionally giving a logfile name)."""
            
        else:
            if self._dolog == val:
                print 'Logging is already',label[val]
            else:
                print 'Switching logging',label[val]
                self._dolog = 1 - self._dolog

    def logstate(self):
        """Print a status message about the logger."""
        try:
            logfile = self.logfname
        except:
            print 'Logging has not been activated.'
        else:
            state = self._dolog and 'active' or 'temporarily suspended'
            print """
File:\t%s
Mode:\t%s
State:\t%s """ % (logfile,self.LOGMODE,state)

        
    def log(self, line,continuation=0):
        """Write the line to a log and create input cache variables _i*."""

        logline=line
        # update the auto _i tables
        #print '***logging line',line # dbg
        #print '***cache_count', self.outputcache.prompt_count # dbg
        if not continuation:
            self._iii = self._ii
            self._ii = self._i
            self._i = self._i00
            # put back the final \n of every input line
            self._i00 = line+'\n'
            self.log_ns['_ih'].append(self._i00)

        # hackish access to top-level namespace to create _i1,_i2... dynamically
        to_main = {'_i':self._i,'_ii':self._ii,'_iii':self._iii}
        if self.do_full_cache:
            in_num = self.outputcache.prompt_count
            # add blank lines if the input cache fell out of sync. This can happen
            # for embedded instances which get killed via C-D and then get resumed.
            while in_num >= len(self.log_ns['_ih']):
                self.log_ns['_ih'].append('\n')
            new_i = '_i'+`in_num`
            if continuation:
                self._i00 = self.log_ns[new_i] +line + '\n'
                self.log_ns['_ih'][in_num] = self._i00
            to_main[new_i] = self._i00
        self.log_ns.update(to_main)

        
        if self._dolog and line:
            #if line.lstrip()[0] in '!@?': logline = '#'+line.lstrip()
            # print 'logging line: ',logline, 'to' ,self.logfile  # dbg
            self.logfile.write(logline+'\n')
            self.logfile.flush()

    def close_log(self):
        if hasattr(self, 'logfile'):
            self.logfile.close()
            self.logfname = ''

#-----------------------------------------------------------------------------
# Changelog:

# 2001. fperez, heavy changes for inclusion in IPython. Documented in more
# detail in the IPython ChangeLog

# Changes to Logger:
# - made the default log filename a parameter

# - put a check for lines beginning with !@? in log(). Needed (even if the
# handlers properly log their lines) for mid-session logging activation to
# work properly. Without this, lines logged in mid session, which get read
# from the cache, would end up 'bare' (with !@? in the open) in the log. Now
# they are caught and prepended with a #.
