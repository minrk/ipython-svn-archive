import os

# import/reload base modules for interactive testing/development
import tctst; reload(tctst)
from tctst import *

import ipythonconfig; reload(ipythonconfig)
from ipythonconfig import IPythonConfig

# Main
c2str = tconfig.configObj2Str

f1 = 'tconfig1.conf'
f2 = 'tconfig2.conf'
c1 = mkConfigObj(f1)
c2 = mkConfigObj(f2)


cat(f1)
cat(f2)
print '><'*40
print c2str(c2)

app1 = App(IPythonConfig,'tconfig1.conf')
app2 = App(IPythonConfig,'tconfig2.conf')

cr1 = RecursiveConfigObj('tconfig1.conf')
os.system('cp tconfig2.conf tconfig2_copy.conf')
cr2 = RecursiveConfigObj('tconfig2_copy.conf')


print '^'*80
print c2str(cr1.conf)
print '-'*80
print c2str(cr2.conf)

ic1 = IPythonConfig(cr1.conf)
ic2 = IPythonConfig(cr2.conf)
print '^'*80
print ic2

# Test use of the hierarchical, coupled manager
print '^-'*40
cr2_fname = 'tconfig2_copy.conf'
cr2 = RecursiveConfigManager(IPythonConfig,cr2_fname)
print '^'*80
print 'Changing m'
print 'm=',cr2.tconf.m
cr2.tconf.m = 101
print 'm=',cr2.tconf.m

print '^'*80
print 'Changing key'
print 'key=',cr2.tconf.Protocol.Handler.key
cr2.tconf.Protocol.Handler.key = "New Key"
print 'key=',cr2.tconf.Protocol.Handler.key
cr2.tconf.Protocol.Handler.key2 = "New Key2"

# Change a few more keys
cr2.tconf.select = 'these'
cr2.tconf.Machine.ip = '99.88.77.66'

# Print the file before/after
print '---------------- BEFORE ------------------'
cat(cr2_fname)
print '++++++++++++++++ AFTER +++++++++++++++++++'
cr2.write()
cat(cr2_fname)
