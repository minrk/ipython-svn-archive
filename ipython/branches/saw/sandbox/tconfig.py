"""Mix of Traits and ConfigObj.
"""

# Stdlib imports

# External imports
from enthought.traits.api import HasTraits, HasStrictTraits, Trait, TraitError,\
     CInt, CFloat, String

from configobj import ConfigObj

# Code begins

# Utility functions
def get_traits(obj):
    skip = set(['trait_added','trait_modified'])
    return [k for k in obj.__class_traits__ if k not in skip]


# Main TConfig class and supporting exceptions
class TConfigError(Exception): pass

class TConfigInvalidKeyError(TConfigError): pass

class TConfig(HasStrictTraits):
    """A class representing configuration objects.

    Note: this class should NOT have any traits itself, since the actual traits
    will be declared by subclasses.  This class is meant to ONLY declare the
    necessary initialization/validation methods.  """
    
    def __init__(self,config):
        """Makes a Traited config object out of a ConfigObj instance
        """
        # Validate the set of keys
        my_traits = set(get_traits(self))
        conf_keys = set(config.keys())
        invalid_keys = conf_keys - my_traits
        if invalid_keys:
            raise TConfigInvalidKeyError("Invalid keys: %s" % invalid_keys)

        # Now set the traits based on the config
        try:
            for k in conf_keys:
                setattr(self,k,config[k])
        except TraitError,e:
            t = self.__class_traits__[k]
            msg = "Bad key,value pair given: %s -> %s\n" % (k,config[k])
            msg += "Expected type: %s" % t.handler.info()
            raise TConfigError(msg)

# Example simple configuration
class MyConfig(TConfig):
    n = CInt
    x = CFloat
    s = String
    
# Example app using this
class App(object):
    def __init__(self,init_only_config,init_config):
        self.rcx = MyConfig(init_only_config)
        self.rc = MyConfig(init_config)


# Testing
if __name__ == '__main__':

    # Normal tests
    good_config = dict(n='3',x='4.15',s='Python')
    t1 = MyConfig(good_config)
    
    fname = 'tconfig1.ini'
    conf = ConfigObj(fname)
    t2 = MyConfig(conf)

    # A few exception-raising tests, turn this later into a doctest that
    # actually runs them, once we settle the exception hirerarchy and format
    if 0:
        bad_config = dict(n='3',bad=10)
        tb1 = MyConfig(bad_config)

        bad_config2 = dict(n='3',x='Not a number',s='Python')
        tb2 = MyConfig(bad_config2)
