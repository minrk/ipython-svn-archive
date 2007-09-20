# import/reload base modules for interactive testing/development
import os

import tctst; reload(tctst)
from tctst import *

import mplconfig; reload(mplconfig)
from mplconfig import MPLConfig

def test_base_file():
    print 'copying mplrc.conf to mplrc_copy.conf'
    os.system('cp mplrc.conf mplrc_copy.conf')
    print 'loading from mplrc_copy.conf'
    mconf = 'mplrc_copy.conf'
    mplconf = TConfigManager(MPLConfig, mconf)
    print 'Backend loaded from file: ', mplconf.tconf.backend.use
    mplconf.tconf.backend.use = 'Cairo'
    print 'Backend now changed to', mplconf.tconf.backend.use, 'in tconfig object'
    print 'writing file'
    mplconf.write()
    print 'reloading from mplrc_copy.conf'
    mplconf = TConfigManager(MPLConfig, mconf)
    print 'Backend reloaded from file: ', mplconf.tconf.backend.use
    print 'It should be Cairo'
    print 'deleting mplrc_copy.conf'
    print '-'*80+'\n'
    os.system('rm mplrc_copy.conf')

test_base_file()

def test_missing_file():
    print 'creating RecursiveConfManager with no_mplrc.conf, which does not exist'
    mconf = 'no_mplrc.conf'
    mplconf = TConfigManager(MPLConfig,mconf)
    print 'calling TConfigManagers write() method'
    mplconf.write()
    print 'Here are the contents of no_mplrc.conf:\n'
    cat('no_mplrc.conf')
    print '\nI might have expected to see the MPLConfig defaults'
    print 'Current numerix:',mplconf.tconf.numerix
    mplconf.tconf.numerix = 'numarray'
    print 'Current numerix:',mplconf.tconf.numerix
    print 'Numerix now:',mplconf.tconf.backend.use
    mplconf.tconf.backend.use = 'Cairo'
    print 'Backend now changed to: ', mplconf.tconf.backend.use
    print 'calling TConfigManagers write() method'
    mplconf.write()
    print 'Here are the new contents of no_mplrc.conf:\n'
    cat('no_mplrc.conf')
    print 'removing no_mplrc.conf'
    print '-'*80+'\n'
    os.system('rm no_mplrc.conf')

test_missing_file()

def test_missing_included_file():
    print 'moving mplrc.conf to mplrc.conf.off'
    os.system('mv mplrc.conf mplrc.conf.off')
    print 'copying mplrc2.conf to mplrc2_copy.conf'
    os.system('cp mplrc2.conf mplrc2_copy.conf')
    mconf = 'mplrc2_copy.conf'
    print 'loading config from mplrc2_copy.conf, which includes mplrc.conf-\n\
    but mplrc.conf does not exist'
    try:
        mplconf = TConfigManager(MPLConfig,mconf)
        print 'here are the contents of mplrc2_copy.conf, as loaded\n'
        os.system('cat mplrc2_copy.conf')
        mplconf.tconf.backend.use = 'Cairo'
        print '\n\nBackend now changed to: ', mplconf.tconf.backend.use
        print 'writing to file'
        mplconf.write()
        print 'Here are the new contents of mplrc2_copy.conf:\n'
        os.system('cat mplrc2_copy.conf')
        print '\n\nI might have expected to see the backend.use here'
        print 'maybe an error should be raised when a config file includes another\n\
        config file that does not exist'
        print 'moving mplrc.conf.off to mplrc.conf, deleting mplrc2_copy.conf'
        print '-'*80+'\n'
    except IOError:
        print 'OK, IOError was raised.'
        os.system('rm mplrc2_copy.conf')
        os.system('mv mplrc.conf.off mplrc.conf')

test_missing_included_file()

