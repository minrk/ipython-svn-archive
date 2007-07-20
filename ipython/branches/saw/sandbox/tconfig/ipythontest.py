from ipythonconfig import IpythonConfig, ConfigManager

class App(object):
    """A trivial 'application' class to be initialized.
    """
    def __init__(self,configClass,configFilename):
        self.rcman = ConfigManager(configClass,configFilename)
        self.rc = self.rcman.tconf

if __name__ == '__main__':

    import os,sys
    from sys import exit
    from pprint import pprint  # dbg
    
    app = App(IpythonConfig,'tconfig2.conf')
    sconf = ConfigManager(AppConfig,'tconfig2.conf')
    
    print app.rc

    # A few exception-raising tests, turn this later into a doctest that
    # actually runs them, once we settle the exception hirerarchy and format
    if 0:
        bad_config = dict(n='3',bad=10)
        tb1 = MyConfig(bad_config)

        bad_config2 = dict(n='3',x='Not a number',s='Python')
        tb2 = MyConfig(bad_config2)

