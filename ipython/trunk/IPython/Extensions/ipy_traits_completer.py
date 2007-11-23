"""Traits-aware tab completion.

This module provides a custom tab-completer that intelligently hides the names
that the enthought.traits library (http://code.enthought.com/traits)
automatically adds to all objects that inherit from its base HasTraits class.


Activation
==========

To use this, put in your ~/.ipython/ipy_user_conf.py file:

    from ipy_traits_completer import activate
    activate([complete_threshold])

The optional complete_threshold argument is the minimal length of text you need
to type for tab-completion to list names that are automatically generated by
traits.  The default value is 3.  Note that at runtime, you can change this
value simply by doing:

    import ipy_traits_completer
    ipy_traits_completer.COMPLETE_THRESHOLD = 4


Usage
=====

The system works as follows.  If t is an empty object that HasTraits, then
(assuming the threshold is at the default value of 3):

In [7]: t.ed<TAB>

doesn't show anything at all, but:

In [7]: t.edi<TAB>
t.edit_traits      t.editable_traits

shows these two names that come from traits.  This allows you to complete on
the traits-specific names by typing at least 3 letters from them (or whatever
you set your threshold to), but to otherwise not see them in normal completion.


Notes
=====

  - This requires Python 2.4 to work (I use sets).  I don't think anyone is
  using traits with 2.3 anyway, so that's OK.
"""

#############################################################################
# External imports
from enthought.traits import api as T

# IPython imports
from IPython.ipapi import TryNext, get as ipget
from IPython.genutils import dir2

#############################################################################
# Module constants

# The completion threshold
# This is currently implemented as a module global, since this sytem isn't
# likely to be modified at runtime by multiple instances.  If needed in the
# future, we can always make it local to the completer as a function attribute.
COMPLETE_THRESHOLD = 3

# Set of names that Traits automatically adds to ANY traits-inheriting object.
# These are the names we'll filter out.
TRAIT_NAMES = set( dir2(T.HasTraits()) ) - set( dir2(object()) )

#############################################################################
# Code begins

def trait_completer(self,event):
    """A custom IPython tab-completer that is traits-aware.

    It tries to hide the internal traits attributes, and reveal them only when
    it can reasonably guess that the user really is after one of them.
    """
    
    #print '\nevent is:',event  # dbg
    symbol_parts = event.symbol.split('.')
    base = '.'.join(symbol_parts[:-1])
    #print 'base:',base  # dbg

    oinfo = self._ofind(base)
    if not oinfo['found']:
        raise TryNext

    obj = oinfo['obj']
    # OK, we got the object.  See if it's traits, else punt
    if not isinstance(obj,T.HasTraits):
        raise TryNext

    # it's a traits object, don't show the tr* attributes unless the completion
    # begins with 'tr'
    attrs = dir2(obj)
    # Now, filter out the attributes that start with the user's request
    attr_start = symbol_parts[-1]
    if attr_start:
        attrs = [a for a in attrs if a.startswith(attr_start)]
    
    # Let's also respect the user's readline_omit__names setting:
    omit__names = ipget().options.readline_omit__names
    if omit__names == 1:
        attrs = [a for a in attrs if not a.startswith('__')]
    elif omit__names == 2:
        attrs = [a for a in attrs if not a.startswith('_')]

    #print '\nastart:<%r>' % attr_start  # dbg

    if len(attr_start)<COMPLETE_THRESHOLD:
        attrs = list(set(attrs) - TRAIT_NAMES)
        
    # The base of the completion, so we can form the final results list
    bdot = base+'.'

    tcomp = [bdot+a for a in attrs]
    #print 'tcomp:',tcomp
    return tcomp

def activate(complete_threshold = COMPLETE_THRESHOLD):
    """Activate the Traits completer.

    :Keywords:
      complete_threshold : int
        The minimum number of letters that a user must type in order to
      activate completion of traits-private names."""
    
    if not (isinstance(complete_threshold,int) and
            complete_threshold>0):
        e='complete_threshold must be a positive integer, not %r'  % \
           complete_threshold
        raise ValueError(e)

    # Set the module global
    global COMPLETE_THRESHOLD
    COMPLETE_THRESHOLD = complete_threshold

    # Activate the traits aware completer
    ip = ipget()
    ip.set_hook('complete_command', trait_completer, re_key = '.*')


#############################################################################
if __name__ == '__main__':
    # Testing/debugging

    # A sorted list of the names we'll filter out
    TNL = list(TRAIT_NAMES)
    TNL.sort()

    # Make a few objects for testing
    class TClean(T.HasTraits): pass
    class Bunch(object): pass
    # A clean traits object
    t = TClean()
    # A nested object containing t
    f = Bunch()
    f.t = t
    # And a naked new-style object
    o = object()

    ip = ipget().IP
    
    # A few simplistic tests

    # Reset the threshold to the default, in case the test is running inside an
    # instance of ipython that changed it
    import ipy_traits_completer
    ipy_traits_completer.COMPLETE_THRESHOLD = 3

    assert ip.complete('t.ed') ==[]

    # For some bizarre reason, these fail on the first time I run them, but not
    # afterwards.  Traits does some really weird stuff at object instantiation
    # time...
    ta = ip.complete('t.edi')
    assert ta == ['t.edit_traits', 't.editable_traits']
    print 'Tests OK'
