# import/reload base modules for interactive testing/development
import os

import tctst; reload(tctst)
from tctst import *

import mplconfig; reload(mplconfig)
from mplconfig import MPLConfig


mconf = 'mplrc.conf'
mplconf = RecursiveConfigManager(MPLConfig, mconf, filePriority=True)
mplconf.tconf.backend.use = 'Qt4Agg'
mplconf.write()

# Check that invalid assignments are not allowed
if 0:
    mplrc = mplconf.tconf
    mplrc.nonsense = 1
    print mplrc


# Make and print to screen the default config
mpc = MPLConfig()
print mpc

# write it out to disk
tconf2File(mpc,'mplrc_default.conf',force=True)

# Create a copy of a hierarchical file, make a simple change, allow interactive
# editing and then write to disk.
os.system('cp mplrc2.conf mplrc2_copy.conf')

mconf2 = 'mplrc2_copy.conf'
mplconf2 = RecursiveConfigManager(MPLConfig,mconf2)

print '-'*80
print 'You can modify the object mplconf2.tconf interactively either'
print 'at the command line, or if you started ipython with -wthread support,'
print 'by typing:'
print 'mplconf2.tconf.edit_traits()'
print 'When finshed, you can save the object to disk via'
print 'mplconf2.write()'
print 'The file it writes is:',mconf2
