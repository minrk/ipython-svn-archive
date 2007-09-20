"""Mix of Traits and ConfigObj.
"""

# Stdlib imports
from inspect import isclass
from pprint import pprint

# External imports
from enthought.traits.api import HasTraits, HasStrictTraits, MetaHasTraits, \
     Trait, TraitError, CInt, CFloat, String, ReadOnly

from configobj import ConfigObj

# Code begins

# Utility functions
def get_traits(obj):
    skip = set(['trait_added','trait_modified'])
    return [k for k in obj.__class_traits__ if k not in skip]

# Alias for naming consistency with configobj conventions
get_scalars = get_traits

def get_sections(obj,sectionClass):
    return [(n,v) for (n,v) in obj.__dict__.iteritems()
            if isclass(v) and issubclass(v,sectionClass)]


# Metaclass hack to avoid exposing ANY GUI dependency, as suggested by R. Kern
# and others on the Enthought-dev list
#class MetaHasStrictTraits(MetaHasTraits, HasStrictTraits):
class MetaHasTraitsNoGUI(MetaHasTraits):
   """ This merges the two metaclasses to avoid conflicts when we later
   multiply inherit from two classes that use each of them.
   """

   def __init__(cls,class_name, bases, class_dict ):
       print '*'*80
       print 'in __init__'
       print 'cls:'
       #pprint(dir(cls))
       print class_name
       #print bases
       print '-'*80
       print 'class_dict:'
       pprint(class_dict)
       print '.'*80
       pprint(dict(cls.__dict__))
       print 'edit:',cls.edit_traits

       #del class_dict['edit_traits']

       super(MetaHasTraitsNoGUI,cls).__init__(class_name,bases,class_dict)


class HasStrictTraitsNoGUI(HasStrictTraits):
   """ This class enables any Python class derived from it to behave like
   HasStrictTraits, but it disables all GUI-related Traits support (traitsui),
   so that instances can be used outside of any GUI toolkit.
   """

   #__metaclass__ = MetaHasTraitsNoGUI

   # Disable GUI support
   def edit_traits(self,*args,**kw):
       print "I'm sorry Dave, I'm afraid I can't do that."

   configure_traits = edit_traits


# Main TConfig class and supporting exceptions
class TConfigError(Exception): pass

class TConfigInvalidKeyError(TConfigError): pass

class TConfig(HasStrictTraitsNoGUI):
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

class ReadOnlyTConfig(HasStrictTraitsNoGUI):
    def __init__(self,tconf):
        tctraits = get_traits(tconf)
        for t in tctraits:
            self.add_trait(t,ReadOnly)
            setattr(self,t,getattr(tconf,t))
    
# Example app using this
class App0(object):
    def __init__(self,init_only_config,init_config):
        self.rcx = ReadOnlyTConfig(MyConfig(init_only_config))
        self.rc = MyConfig(init_config)

# More complex application config
#class TConfig2(HasStrictTraitsNoGUI):
class TConfig2(HasTraits):
    """A class representing configuration objects.

    Note: this class should NOT have any traits itself, since the actual traits
    will be declared by subclasses.  This class is meant to ONLY declare the
    necessary initialization/validation methods.  """
    
    def __init__(self,config):
        """Makes a Traited config object out of a ConfigObj instance
        """
        # Validate the set of scalars ...
        my_scalars = set(get_scalars(self))
        cf_scalars = set(config.scalars)
        invalid_scalars = cf_scalars - my_scalars
        if invalid_scalars:
            raise TConfigInvalidKeyError("Invalid keys: %s" % invalid_scalars)
        # ... and sections
        my_sections1 = get_sections(self.__class__,TConfig2)
        my_sections = set([n for n,v in my_sections1])
        cf_sections = set(config.sections)
        invalid_sections = cf_sections - my_sections
        if invalid_sections:
            raise TConfigInvalidKeyError("Invalid sections: %s" %
                                         invalid_sections)

        # Now set the traits based on the config
        try:
            for k in cf_scalars:
                setattr(self,k,config[k])
        except TraitError,e:
            t = self.__class_traits__[k]
            msg = "Bad key,value pair given: %s -> %s\n" % (k,config[k])
            msg += "Expected type: %s" % t.handler.info()
            raise TConfigError(msg)

        # And build subsections
        for s,v in my_sections1:
            setattr(self,s,v(config[s]))



class ReadOnlyTConfig2:
    pass

class AppConfig(TConfig2):

    m = CInt
    
    class InitOnly(TConfig2,ReadOnlyTConfig2):
        n = CInt
        x = CFloat

    class Protocol(TConfig2):
        ptype = String

        class Handler(TConfig2):
            key = String

    class Machine(TConfig2):
        ip = String
        port = CInt

class App(object):
    def __init__(self,conf_filename):
        conf = ConfigObj(conf_filename)
        self.rc = AppConfig(conf)

        #self.rc = mkConfig(AppConfig,conf_filename)


# Testing
if __name__ == '__main__':

    # Normal tests
    conf0 = dict(n='3',x='4.15',s='Python')
    t1 = MyConfig(conf0)
    
    fname = 'tconfig1.ini'
    conf1 = ConfigObj(fname)
    t2 = MyConfig(conf1)

    app0 = App0(conf0,conf1)


    fname2 = 'tconfig2.conf'
    conf2 = ConfigObj(fname2)
    app1 = App(fname2)

    # A few exception-raising tests, turn this later into a doctest that
    # actually runs them, once we settle the exception hirerarchy and format
    if 0:
        bad_config = dict(n='3',bad=10)
        tb1 = MyConfig(bad_config)

        bad_config2 = dict(n='3',x='Not a number',s='Python')
        tb2 = MyConfig(bad_config2)
