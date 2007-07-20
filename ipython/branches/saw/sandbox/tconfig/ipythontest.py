# import/reload base modules for interactive testing/development
import tctst; reload(tctst)
from tctst import *

import ipythonconfig; reload(ipythonconfig)
from ipythonconfig import IPythonconfig

# Main
app = App(IPythonconfig,'tconfig2.conf')
sconf = ConfigManager(IPythonconfig,'tconfig2.conf')

print app.rc
