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
import textwrap

############################################################################
# External imports
############################################################################
from enthought.traits import api as T

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

def mkConfigObjRec(filename,components=None):
    """Return a ConfigObj using our conventions. Supports recursive inclusion.

    This version supports the special key include="path/to/file" in the config
    files (only at the top level of each), and will recursively load the
    requested files.

    :Return:
      A ConfigObj instance, built with the conventions of mkConfigObj, and
      computed recursively.  The recursion process loads the included files
      first, and then applies the outermost configuration on top of them.  The
      derived files therefore override any flags in the included ones.

    :Parameters:

      filename : string
        File to read from.

    :Keywords:

      components : list (None)

        If given, this list is filled with the individual ConfigObj instances
        corresponding to each file loaded, without any inter-file overwrites.
        The return value of the whole function contains the result of doing a
        'telescoping update' with this list, starting with the last entry (the
        'deepest' one) and updating it with each successive entry.  Having this
        list of unmodified instances can be used by code which wants to map
        changes made at runtime to their original files or objects.
    """

    conf = mkConfigObj(filename)
    
    # Do recursive loading. We only allow (or at least honor) the include tag
    # at the top-level.  For now, we drop the inclusion information so that
    # there are no restrictions on which levels of the TConfig hierarchy can
    # use include statements.  But this means that

    if components is not None:
        # if bookkeeping of each separate component of the recursive
        # construction was requested, make a separate object for storage
        # there, since we don't want that to be modified by the inclusion
        # process.
        components.append(mkConfigObj(filename))

    incfname = conf.pop('include',None)
    if incfname is not None:
        # Do recursive load

        confinc = mkConfigObjRec(incfname,components)
        
        # Update with self to get proper ordering (included files provide base
        # data, current one overwrites)
        confinc.update(conf)
        # And do swap to return the updated structure
        conf = confinc
        # Set the filename to be the original file instead of the included one
        conf.filename = filename

    return conf

class RecursiveConfigObj(object):
    """Object-oriented interface for recursive ConfigObj constructions."""

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

############################################################################
# Main TConfig class and supporting exceptions
############################################################################

class TConfigError(Exception): pass

class TConfigInvalidKeyError(TConfigError): pass

class TConfigSection(T.HasStrictTraits):
    def __repr__(self,depth=0):
        """Dump a self section to a string."""

        indent = '    '*max(depth-1,0)

        try:
            top_name = self.__class__.__original_name__
        except AttributeError:
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
            except KeyError:
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

            # We must use add_trait instead of setattr because we inherit from
            # HasStrictTraits, but we need to then do a 'dummy' getattr call on
            # self so the class trait propagates to the instance.
            self.add_trait(s,section)
            getattr(self,s)

class ConfigManager(object):
    """A simple object to manage and sync a TConfig and a ConfigObj pair.
    """
    
    def __init__(self,configClass,configFilename,filePriority=True):
        """Make a new ConfigManager.

        :Paramters:
        
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
        return configObj2Str(self.fconf)

    __repr__ = __str__ = fconfStr
