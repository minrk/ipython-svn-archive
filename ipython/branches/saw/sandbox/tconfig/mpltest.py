# import/reload base modules for interactive testing/development
import tconfig, mplconfig
reload(tconfig)
reload(mplconfig)

from tconfig import ConfigManager, mkConfigObj
from mplconfig import MPLConfig

class App(object):
    """A trivial 'application' class to be initialized.
    """
    def __init__(self,configClass,configFilename):
        self.rcman = ConfigManager(configClass,configFilename)
        self.rc = self.rcman.tconf

if __name__ == '__main__':

    import os
    from pprint import pprint  # dbg
    
    app = App(MPLConfig,'mpl2.conf')
    
    print app.rc
    
    # some more examples:
    print '-'*80
    print "Here is a default mpl config generated purely from the code:"
    mplrc = MPLConfig()
    print mplrc

    print '-'*80
    print "And here is a modified one, using a config file that only changes"
    print "a few parameters and otherwise uses the defaults:"
    mpl2conf = mkConfigObj('mpl2.conf')
    mplrc2 = MPLConfig(mpl2conf)
    print mplrc2

    # An example of the ConfigManager usage.
    m3conf = 'mpl3.conf'
    if os.path.isfile(m3conf):
        os.unlink(m3conf)
    mplconf = ConfigManager(MPLConfig,m3conf)
    mplconf.write()
    print '-'*80
    print "The file %r was written to disk..." % m3conf
    os.system('more %s' % m3conf)
    
    if 0:
        print '-'*80
        print "Play with the 'mpl' object a little, esp its .rc attribute..."
        print "You can even do mpl.rc.edit_traits() if you are running in "
        print "ipython -wthread.  It only works with the top-level for now."
        print
        print "The following is an auto-generated dump of the rc object."
        print "Note that this remains valid input for an rc file:"
        print
        mpl = App(MPLConfig,'mpl.conf')
        print mpl.rc
