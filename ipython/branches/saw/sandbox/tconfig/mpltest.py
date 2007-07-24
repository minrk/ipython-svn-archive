# import/reload base modules for interactive testing/development
import tctst; reload(tctst)
from tctst import *

import mplconfig; reload(mplconfig)
from mplconfig import MPLConfig


m3conf = 'mplrc.conf'
mplconf = ConfigManager(MPLConfig, m3conf, filePriority=True)
mplconf.tconf.backend.use = 'Qt4Agg'
mplconf.write()

# Make and print to screen the default config
mpc = MPLConfig()
print mpc

##mplrc = mplconf.tconf
##
##mplrc.nonsense = 1
##
##print mplrc
