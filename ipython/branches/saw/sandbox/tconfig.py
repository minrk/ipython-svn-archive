"""Mix of Traits and ConfigObj.

TODO:

  - Finish the ConfigManager class that holds a reference to BOTH the ConfigObj
  and the TConfig, and that automatically hooks traits listeners, so that all
  traits actions on the TConfig get propagated back to the ConfigObj.  This
  will let us write the config file back to disk from within the app.

  This code already works: the files *do* get written correctly always, but at
  the price of a full object update at write time.  Hooking up traits listeners
  would be a bit more elegant, though at this point it isn't too high priority.

  - Automatically construct a view for the TConfig hierarchies, so that we get
  proper editing with Traits beyond the first level (try mpl.rc.edit_traits()
  to see the problem).
"""

############################################################################
# Stdlib imports
############################################################################
from cStringIO import StringIO
from inspect import isclass

############################################################################
# External imports
############################################################################
from enthought.traits.api import HasTraits, HasStrictTraits, MetaHasTraits, \
     Trait, TraitError, Bool, Int, Float, Str, ReadOnly, ListFloat

import configobj

############################################################################
# Utility functions
############################################################################

def mkConfigObj(filename):
    """Return a ConfigObj instance with our hardcoded conventions.

    Use a simple factory that wraps our option choices for using ConfigObj.
    I'm hard-wiring certain choices here, so we'll always use instances with
    THESE choices.
    """
    return configobj.ConfigObj(filename,
                               create_empty=True,
                               indent_type='    ',
                               interpolation='Template',
                               unrepr=True)

nullConf = mkConfigObj(None)

def mk_scalars(sc):
    """ input sc MUST be sorted!!!"""
    scalars = []
    maxi = len(sc)-1
    i = 0
    while i<len(sc):
        t = sc[i]
        if i<maxi and t+'_' == sc[i+1]:
            # skip one ahead in the loop, to skip over the names of shadow
            # traits, which we don't want to expose in the config files.
            i += 1
        scalars.append(t)
        i += 1
    return scalars

def get_scalars(obj):
    """Return scalars for a TConf class object"""

    skip = set(['trait_added','trait_modified'])
    sc = [k for k in obj.trait_names() if k not in skip]
    sc.sort()
    return mk_scalars(sc)

def get_sections(obj,sectionClass):
    """Return sections for a TConf class object"""
    return [(n,v) for (n,v) in obj.__dict__.iteritems()
            if isclass(v) and issubclass(v,sectionClass)]

def partition_instance(obj):
    """Return scalars,sections for a given TConf instance.
    """
    scnames = []
    sections = []
    for k,v in obj.__dict__.iteritems():
        if isinstance(v,TConfigSection):
            sections.append((k,v))
        else:
            scnames.append(k)

    scnames.sort()
    scnames = mk_scalars(scnames)
    scalars = [(s,obj.__dict__[s]) for s in scnames]

    return scalars, sections

############################################################################
# Main TConfig class and supporting exceptions
############################################################################
class TConfigError(Exception): pass

class TConfigInvalidKeyError(TConfigError): pass

class TConfigSection(HasTraits):
    def __repr__(self,depth=0):
        """Dump a self section to a string."""

        indent = '    '*max(depth-1,0)

        try:
            top_name = self.__class__.__original_name__
        except AttributeError:
            top_name = self.__class__.__name__

        if depth == 0:
            label = '# Dump of %s\n' % top_name
        else:
            label = '\n'+indent+('[' * depth) + top_name + (']'*depth)

        out = [label]

        scalars, sections = partition_instance(self)

        for s,v in scalars:
            out.append(indent+('%s = %r' % (s,v)))

        for sname,sec in sections:
            out.append(sec.__repr__(depth+1))

        return '\n'.join(out)
    

class TConfig(TConfigSection):
    """A class representing configuration objects.

    Note: this class should NOT have any traits itself, since the actual traits
    will be declared by subclasses.  This class is meant to ONLY declare the
    necessary initialization/validation methods.  """
    
    def __init__(self,config=nullConf):
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
            for k in my_scalars:
                try:
                    setattr(self,k,config[k])
                except KeyError:
                    # This seems silly, but it forces some of Trait's magic to
                    # fire and actually set the value on the instance in such a
                    # way that it will later be properly read by introspection
                    # tools. 
                    getattr(self,k)
        except TraitError,e:
            t = self.__class_traits__[k]
            msg = "Bad key,value pair given: %s -> %s\n" % (k,config[k])
            msg += "Expected type: %s" % t.handler.info()
            raise TConfigError(msg)

        # And build subsections
        for s,v in section_items:
            try:
                section = v(config[s])
            except KeyError:
                section = v()
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

class ConfigManager(object):
    """A simple object to manage and sync a TConfig and a ConfigObj pair.
    """
    
    def __init__(self,configClass,configFilename,filePriority=True):
        """Make a new ConfigManager.

        :Paramters:
          configClass : class

          configFilename : string

        :Keywords:
          filePriority : bool (True)

            If true, at construction time the file object takes priority and
            overwrites the contents of the config object.  Else, the data flow
            is reversed and the file object will be overwritten with the
            configClass defaults at write() time.
        """
        
        self.fconf = mkConfigObj(configFilename)
        if filePriority:
            self.tconf = configClass(self.fconf)
        else:
            self.tconf = configClass(nullConf)
            self.fconfUpdate(self.fconf,self.tconf)

    def fconfUpdate(self,fconf,tconf):
        """Update the fconf object with the data from tconf"""

        scalars, sections = partition_instance(tconf)

        for s,v in scalars:
            fconf[s] = v

        for secname,sec in sections:
            self.fconfUpdate(fconf.setdefault(secname,{}),sec)

    def write(self):
        self.fconfUpdate(self.fconf,self.tconf)
        self.fconf.write()

    def tconfStr(self):
        return str(self.tconf)

    def fconfStr(self):
        outstr = StringIO()
        self.fconfUpdate(self.fconf,self.tconf)
        self.fconf.write(outstr)
        return outstr.getvalue()

    __repr__ = __str__ = fconfStr

############################################################################
# Testing/example
############################################################################
if __name__ == '__main__':

    import os
    from pprint import pprint  # dbg
    

    class App(object):
        """A trivial 'application' class to be initialized.
        """
        def __init__(self,configClass,configFilename):
            self.rcman = ConfigManager(configClass,configFilename)
            self.rc = self.rcman.tconf

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
        interactive = Bool(True)
        
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
            edgecolor = Trait('violet',standard_color)

            class subplot(TConfig):
                """The figure subplot parameters.  All dimensions are fraction
                of the figure width or height"""
                left = Float(0.125)
                right = Float(0.9)
                bottom = Float(0.1)
                top = Float(0.9)


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

    # A few exception-raising tests, turn this later into a doctest that
    # actually runs them, once we settle the exception hirerarchy and format
    if 0:
        bad_config = dict(n='3',bad=10)
        tb1 = MyConfig(bad_config)

        bad_config2 = dict(n='3',x='Not a number',s='Python')
        tb2 = MyConfig(bad_config2)
