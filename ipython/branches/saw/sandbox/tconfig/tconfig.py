"""Mix of Traits and ConfigObj.

Provides:

- Coupling a Traits object to a ConfigObj one, so that changes to the Traited
  instance propagate back into the ConfigObj.

- A declarative interface for describing configurations that automatically maps
  to valid ConfigObj representations.

- From these descriptions, valid .conf files can be auto-generated, with class
  docstrings and traits information used for initial auto-documentation.

- Hierarchical inclusion of files, so that a base config can be overridden only
  in specific spots.

- Automatic GUI editing of configuration objects.


TODO:

  - turn the currently interactive tests into proper doc/unit tests.
"""

__license__ = 'BSD'

############################################################################
# Stdlib imports
############################################################################
from cStringIO import StringIO
from inspect import isclass
import textwrap

############################################################################
# External imports
############################################################################
from enthought.traits import api as T

# For now we ship this internally so users don't have to download it, since
# it's just a single-file dependency.
import configobj

############################################################################
# Utility functions
############################################################################

def dedent(txt):
    """A modified version of textwrap.dedent, specialized for docstrings.

    This version doesn't get confused by the first line of text having
    inconsistent indentation from the rest, which happens a lot in docstrings.

    :Examples:

        >>> s = '''
        ... First line.
        ... More...
        ... End'''

        >>> print dedent(s)
        First line.
        More...
        End

        >>> s = '''First line
        ... More...
        ... End'''

        >>> print dedent(s)
        First line
        More...
        End
    """
    out = [textwrap.dedent(t) for t in txt.split('\n',1)
           if t and not t.isspace()]
    return '\n'.join(out)

def comment(strng,indent=''):
    """return an input string, commented out"""
    template = indent + '# %s'
    lines = [template % s for s in strng.splitlines(True)]
    return ''.join(lines)

def short_str(txt,line_length=80,max_lines=6):
    """Shorten a text input if necessary.
    """

    assert max_lines%2==0,"max_lines must be even"

    if txt.count('\n') <= 1:
        # Break up auto-generated text that can be *very* long but in just one
        # line.
        ltxt = len(txt)
        max_len = line_length*max_lines
        chunk = max_lines/2

        if ltxt > max_len:
            out = []
            for n in range(chunk):
                out.append(txt[line_length*n:line_length*(n+1)])

            out.append(' <...snipped %d chars...> ' % (ltxt-max_len))

            for n in range(-chunk-1,0,1):
                # Special-casing for the last step of the loop, courtesy of
                # Python's idiotic string slicign semantics when the second
                # argument is 0.  Argh.
                end = line_length*(n+1)
                if end==0: end = None
                out.append(txt[line_length*n:end])

            txt = '\n'.join(out)
        else:
            nlines = ltxt/line_length
            out = [ txt[line_length*n:line_length*(n+1)]
                    for n in range(nlines+1)]
            if out:
                txt = '\n'.join(out)
    return txt

def configObj2Str(cobj):
    """Dump a Configobj instance to a string."""
    outstr = StringIO()
    cobj.write(outstr)
    return outstr.getvalue()

def filter_scalars(sc):
    """ input sc MUST be sorted!!!"""
    scalars = []
    maxi = len(sc)-1
    i = 0
    while i<len(sc):
        t = sc[i]
        if t.startswith('_tconf_'):
            i += 1
            continue
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
    return filter_scalars(sc)

def get_sections(obj,sectionClass):
    """Return sections for a TConf class object"""
    return [(n,v) for (n,v) in obj.__dict__.iteritems()
            if isclass(v) and issubclass(v,sectionClass)]

def get_instance_sections(inst):
    """Return sections for a TConf instance"""
    sections = [(k,v) for k,v in inst.__dict__.iteritems()
                if isinstance(v,TConfigSection) and not k=='_tconf_parent']
    # Sort the sections by name
    sections.sort(key=lambda x:x[0])
    return sections

def partition_instance(obj):
    """Return scalars,sections for a given TConf instance.
    """
    scnames = []
    sections = []
    for k,v in obj.__dict__.iteritems():
        if isinstance(v,TConfigSection):
            if not k=='_tconf_parent':
                sections.append((k,v))
        else:
            scnames.append(k)

    # Sort the sections by name
    sections.sort(key=lambda x:x[0])

    # Sort the scalar names, filter them and then extract the actual objects
    scnames.sort()
    scnames = filter_scalars(scnames)
    scalars = [(s,obj.__dict__[s]) for s in scnames]
    
    return scalars, sections

def mkConfigObj(filename):
    """Return a ConfigObj instance with our hardcoded conventions.

    Use a simple factory that wraps our option choices for using ConfigObj.
    I'm hard-wiring certain choices here, so we'll always use instances with
    THESE choices.

    :Parameters:

      filename : string
        File to read from.
    """
    return configobj.ConfigObj(filename,
                               create_empty=True,
                               indent_type='    ',
                               interpolation='Template',
                               unrepr=True)

nullConf = mkConfigObj(None)

class RecursiveConfigObj(object):
    """Object-oriented interface for recursive ConfigObj constructions."""

    def __init__(self,filename):
        """Return a ConfigObj instance with our hardcoded conventions.

        Use a simple factory that wraps our option choices for using ConfigObj.
        I'm hard-wiring certain choices here, so we'll always use instances with
        THESE choices.

        :Parameters:

          filename : string
            File to read from.
        """

        self.comp = []
        self.conf = self._load(filename)

    def _load(self,filename):
        conf = mkConfigObj(filename)

        # Do recursive loading. We only allow (or at least honor) the include
        # tag at the top-level.  For now, we drop the inclusion information so
        # that there are no restrictions on which levels of the TConfig
        # hierarchy can use include statements.  But this means that

        # if bookkeeping of each separate component of the recursive
        # construction was requested, make a separate object for storage
        # there, since we don't want that to be modified by the inclusion
        # process.
        self.comp.append(mkConfigObj(filename))

        incfname = conf.pop('include',None)
        if incfname is not None:
            # Do recursive load

            confinc = self._load(incfname)

            # Update with self to get proper ordering (included files provide
            # base data, current one overwrites)
            confinc.update(conf)
            # And do swap to return the updated structure
            conf = confinc
            # Set the filename to be the original file instead of the included
            # one
            conf.filename = filename
        return conf
        
############################################################################
# Main TConfig class and supporting exceptions
############################################################################

class TConfigError(Exception): pass

class TConfigInvalidKeyError(TConfigError): pass

class TConfigSection(T.HasStrictTraits):

    _tconf_parent = T.Any
    
    def __repr__(self,depth=0):
        """Dump a section to a string."""

        indent = '    '*max(depth-1,0)

        top_name = self.__class__.__name__

        if depth == 0:
            label = '# %s - plaintext (in .conf format)\n' % top_name
        else:
            label = '\n'+indent+('[' * depth) + top_name + (']'*depth)

        out = [label]

        doc = self.__class__.__doc__
        if doc is not None:
            out.append(comment(dedent(doc),indent))

        scalars, sections = partition_instance(self)

        for s,v in scalars:
            try:
                info = self.__base_traits__[s].handler.info()
                # Get a short version of info with lines of max. 78 chars, so
                # that after commenting them out (with '# ') they are at most
                # 80-chars long.
                out.append(comment(short_str(info,78-len(indent)),indent))
            except (KeyError,AttributeError):
                pass
            out.append(indent+('%s = %r' % (s,v)))

        for sname,sec in sections:
            out.append(sec.__repr__(depth+1))

        return '\n'.join(out)

class TConfig(TConfigSection):
    """A class representing configuration objects.

    Note: this class should NOT have any traits itself, since the actual traits
    will be declared by subclasses.  This class is meant to ONLY declare the
    necessary initialization/validation methods.  """
    
    def __init__(self,config=nullConf,parent=None,monitor=None):
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

        self._tconf_parent = parent

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
                scal = getattr(self,k)
        except T.TraitError,e:
            t = self.__class_traits__[k]
            msg = "Bad key,value pair given: %s -> %s\n" % (k,config[k])
            msg += "Expected type: %s" % t.handler.info()
            raise TConfigError(msg)            

        # And build subsections
        for s,v in section_items:
            try:
                section = v(config[s],self,monitor=monitor)
            except KeyError:
                section = v()

            # We must use add_trait instead of setattr because we inherit from
            # HasStrictTraits, but we need to then do a 'dummy' getattr call on
            # self so the class trait propagates to the instance.
            self.add_trait(s,section)
            getattr(self,s)

        if monitor: self.on_trait_change(monitor)

##############################################################################
# High-level class(es) and utilities for handling a coupled pair of TConfig and
# ConfigObj instances.
##############################################################################

def path_to_root(obj):
    """Find the path to the root of a nested TConfig instance."""
    ob = obj
    path = []
    while ob._tconf_parent is not None:
        path.append(ob.__class__.__name__)
        ob = ob._tconf_parent
    path.reverse()
    return path

def set_value(fconf,path,key,value):
    """Set a value on a ConfigObj instance, arbitrarily deep."""
    section = fconf
    for sname in path:
        section = section.setdefault(sname,{})
    section[key] = value


def fmonitor(fconf):
    """Make a monitor for coupling TConfig instances to ConfigObj ones.

    We must use a closure because Traits makes assumptions about the functions
    used with on_trait_change() that prevent the use of a callable instance.
    """
    
    def mon(obj,name,new):
        set_value(fconf,path_to_root(obj),name,new)
        
    return mon

class RecursiveConfigManager(object):
    """A simple object to manage and sync a TConfig and a ConfigObj pair.
    """
    
    def __init__(self,configClass,configFilename,filePriority=True):
        """Make a new ConfigManager.

        :Parameters:
        
          configClass : class

          configFilename : string
            If the filename points to a non-existent file, it will be created
            empty.  This is useful when creating a file form from an existing
            configClass with the class defaults.


        :Keywords:

          filePriority : bool (True)

            If true, at construction time the file object takes priority and
            overwrites the contents of the config object.  Else, the data flow
            is reversed and the file object will be overwritten with the
            configClass defaults at write() time.
        """

        rconf = RecursiveConfigObj(configFilename)
        # In a hierarchical object, the two following fconfs are *very*
        # different.  In self.fconf, we'll keep the outer-most fconf associated
        # directly to the original filename.  self.fconfCombined, instead,
        # contains an object which has the combined effect of having merged all
        # the called files in the recursive chain.
        self.fconf = rconf.comp[0]
        self.fconfCombined = rconf.conf

        # Create a monitor to track and apply trait changes to the tconf
        # instance over into the fconf one
        monitor = fmonitor(self.fconf)
        
        if filePriority:
            self.tconf = configClass(self.fconfCombined,monitor=monitor)
        else:
            # Push defaults onto file object
            self.tconf = configClass(nullConf,monitor=monitor)
            self.fconfUpdate(self.fconf,self.tconf)

    def fconfUpdate(self,fconf,tconf):
        """Update the fconf object with the data from tconf"""

        scalars, sections = partition_instance(tconf)

        for s,v in scalars:
            fconf[s] = v

        for secname,sec in sections:
            self.fconfUpdate(fconf.setdefault(secname,{}),sec)

    def write(self,filename=None):
        """Write out to disk.

        This method writes out only to the top file in a hierarchical
        configuration, which means that the class defaults and other values not
        explicitly set in the top level file are NOT written out.

        :Keywords:
        
          filename : string (None)
            If given, the output is written to this file, otherwise the
            .filename attribute of the top-level configuration object is used.
        """
        if filename is not None:
            fileObj = open(filename,'w')
            out = self.fconf.write(fileObj)
            fileObj.close()
            return out
        else:
            return self.fconf.write()


    def writeAll(self,filename=None):
        """Write out the entire configuration to disk.

        This method, in contrast with write(), updates the .fconfCombined
        object with the *entire* .tconf instance, and then writes it out to
        disk.  This method is thus useful for generating files that contain an
        self-contained, non-hierarchical file.

        :Keywords:
        
          filename : string (None)
            If given, the output is written to this file, otherwise the
            .filename attribute of the top-level configuration object is used.
        """
        if filename is not None:
            fileObj = open(filename,'w')
            self.fconfUpdate(self.fconfCombined,self.tconf)
            out = self.fconf.write(fileObj)
            fileObj.close()
            return out
        else:
            self.fconfUpdate(self.fconfCombined,self.tconf)
            return self.fconf.write()

    def tconfStr(self):
        return str(self.tconf)

    def fconfStr(self):
        return configObj2Str(self.fconf)

    __repr__ = __str__ = fconfStr
