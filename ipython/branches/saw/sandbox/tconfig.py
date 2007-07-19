"""Mix of Traits and ConfigObj.
"""

############################################################################
# Stdlib imports
############################################################################
from inspect import isclass
#from pprint import pprint  # dbg


############################################################################
# External imports
############################################################################
from enthought.traits.api import HasTraits, HasStrictTraits, MetaHasTraits, \
     Trait, TraitError, Bool, Int, Float, Str, ReadOnly, ListFloat

import configobj


############################################################################
# Utility functions
############################################################################

def get_scalars(obj):
    """Return scalars for a TConf class object"""
    
    skip = set(['trait_added','trait_modified'])
    return [k for k in obj.__class_traits__ if k not in skip]

def get_sections(obj,sectionClass):
    """Return sections for a TConf class object"""
    return [(n,v) for (n,v) in obj.__dict__.iteritems()
            if isclass(v) and issubclass(v,sectionClass)]

def partition_instance(obj):
    """Return scalars,sections for a given TConf instance.
    """
    scalars = []
    sections = []
    for k,v in obj.__dict__.iteritems():
        if isinstance(v,TConfigSection):
            sections.append(v)
        else:
            scalars.append(k)

    return scalars, sections

def tsecDump(tconf,depth=0):
    """Dump a tconf section to a string."""
    
    indent = '    '*max(depth-1,0)

    try:
        top_name = tconf.__class__.__original_name__
    except AttributeError:
        top_name = tconf.__class__.__name__

    if depth == 0:
        label = '# Dump of %s\n' % top_name
    else:
        label = '\n'+indent+('[' * depth) + top_name + (']'*depth)

    out = [label]

    scalars, sections = partition_instance(tconf)

    for s in scalars:
        v = getattr(tconf,s)
        out.append(indent+('%s = %r' % (s,v)))

    for sec in sections:
        out.extend(tsecDump(sec,depth+1))

    return out
    

def tconfDump(tconf):
    """Dump a tconf object to a string"""

    tstr = []
    tstr.extend(tsecDump(tconf,depth=0))
    return '\n'.join(tstr)

def tconfPrint(tconf):
    """Print a tconf object."""
    print tconfDump(tconf)
    

def mkConfigObj(filename):
    """Return a ConfigObj instance with our hardcoded conventions.

    Use a simple factory that wraps our option choices for using ConfigObj.
    I'm hard-wiring certain choices here, so we'll always use instances with
    THESE choices.
    """
    return configobj.ConfigObj(filename,
                               file_error=True,
                               interpolation='Template',
                               unrepr=True)

############################################################################
# Main TConfig class and supporting exceptions
############################################################################
class TConfigSection(HasTraits): pass

class TConfigError(Exception): pass

class TConfigInvalidKeyError(TConfigError): pass

class TConfig(TConfigSection):
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
        section_items = get_sections(self.__class__,TConfig)
        my_sections = set([n for n,v in section_items])
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
        for s,v in section_items:
            section = v(config[s])
            if issubclass(v,ReadOnlyTConfig):
                section = ReadOnlyTConfig(section)
                # XXX - Hack the name back in place.  This should be fixed and
                # done more cleanly via a proper inheritance hierarchy, but I
                # kept having problems with that approach due to the fact that
                # the ReadOnly class needs to create a bunch of ReadOnly traits
                # out of traits that have already been validated.  So it
                # fundamentally needs to be a different class.  The purely
                # declarartive nature of how I'm using Traits here makes this
                # type of situation particularly difficult.
                section.__class__.__original_name__ = s

            setattr(self,s,section)

class ReadOnlyTConfig(TConfigSection):
    """Make a TConfigSection object with ALL ReadOnly traits.
    """
    def __init__(self,tconf):
        tctraits = get_scalars(tconf)
        for t in tctraits:
            self.add_trait(t,ReadOnly)
            setattr(self,t,getattr(tconf,t))

############################################################################
# Testing/example
############################################################################
if __name__ == '__main__':

    class App(object):
        """A trivial 'application' class to be initialized.
        """
        def __init__(self,configClass,conf_filename):
            conf = mkConfigObj(conf_filename)
            self.rc = configClass(conf)

    # Example of an application configuration and the app using it
    class AppConfig(TConfig):

        m = Int

        class InitOnly(TConfig,ReadOnlyTConfig):
            n = Int
            x = Float

        class Protocol(TConfig):
            ptype = Str

            class Handler(TConfig):
                key = Str

        class Machine(TConfig):
            ip = Str
            port = Int

    simpleapp = App(AppConfig,'tconfig2.conf')


    # A matplotlib-like example

    standard_color = Trait ('black',
                            {'black': (0.0, 0.0, 0.0, 1.0),
                             'blue': (0.0, 0.0, 1.0, 1.0),
                             'cyan': (0.0, 1.0, 1.0, 1.0),
                             'green': (0.0, 1.0, 0.0, 1.0),
                             'magenta': (1.0, 0.0, 1.0, 1.0),
                             'orange': (0.8, 0.196, 0.196, 1.0),
                             'purple': (0.69, 0.0, 1.0, 1.0),
                             'red': (1.0, 0.0, 0.0, 1.0),
                             'violet': (0.31, 0.184, 0.31, 1.0),
                             'yellow': (1.0, 1.0, 0.0, 1.0),
                             'white': (1.0, 1.0, 1.0, 1.0),
                             'transparent': (1.0, 1.0, 1.0, 0.0) } )

    class MPLConfig(TConfig):

        # Valid backends, first is default
        backend = Trait('TkAgg','WXAgg','GTKAgg','QtAgg','Qt4Agg')
        interactive = Bool(False)
        
        class InitOnly(TConfig,ReadOnlyTConfig):
            """Things that can only be set at init time"""
            numerix = Str('numpy')

        class lines(TConfig):
            linewidth = Float(2.0)
            linestyle = Trait('-','=','^')

        class figure(TConfig):
            figsize = ListFloat([6.4,4.8])  # figure size in inches
            dpi = Int(100)            # figure dots per inch
            facecolor = Float(0.75)    # figure facecolor; 0.75 is scalar gray
            edgecolor = Trait('white',standard_color)

            class subplot(TConfig):
                """The figure subplot parameters.  All dimensions are fraction
                of the figure width or height"""
                left = Float(0.125)
                right = Float(0.9)
                bottom = Float(0.1)
                top = Float(0.9)

    mpl = App(MPLConfig,'mpl.conf')
    print "Play with the 'mpl' object a little, esp its .rc attribute..."
    print "You can even do mpl.rc.edit_traits() if you are running in "
    print "ipython -wthread.  It only works with the top-level for now."
    print
    print "The following is an auto-generated dump of the rc object."
    print "Note that this remains valid input for an rc file:"
    print
    tconfPrint(mpl.rc)

    # A few exception-raising tests, turn this later into a doctest that
    # actually runs them, once we settle the exception hirerarchy and format
    if 0:
        bad_config = dict(n='3',bad=10)
        tb1 = MyConfig(bad_config)

        bad_config2 = dict(n='3',x='Not a number',s='Python')
        tb2 = MyConfig(bad_config2)
