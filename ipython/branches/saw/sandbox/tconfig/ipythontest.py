# import/reload base modules for interactive testing/development
import tctst; reload(tctst)
from tctst import *

import ipythonconfig; reload(ipythonconfig)
from ipythonconfig import IPythonConfig

# Main
c2str = tconfig.configObj2Str

def cat(fname):
    print '### FILENAME:',fname
    print open(fname).read()


f1 = 'tconfig1.conf'
f2 = 'tconfig2.conf'
c1 = mkConfigObj(f1)
c2 = mkConfigObj(f2)


cat(f1)
cat(f2)
print '><'*40
print c2str(c2)

#sys.exit()

#app1 = App(IPythonConfig,'tconfig1.conf')
#app2 = App(IPythonConfig,'tconfig2.conf')

cr1 = RecursiveConfigObj('tconfig1.conf')
cr2 = RecursiveConfigObj('tconfig2.conf')

print '^'*80
print c2str(cr1.conf)
print '-'*80
print c2str(cr2.conf)

ic1 = IPythonConfig(cr1.conf)
ic2 = IPythonConfig(cr2.conf)
print '^'*80
print ic2
