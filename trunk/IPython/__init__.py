"""
IPython -- An enhanced Interactive Python

One of Python's nicest features is its interactive interpreter. This allows
very fast testing of ideas without the overhead of creating test files as is
typical in most programming languages. However, the interpreter supplied with
the standard Python distribution is fairly primitive (and IDLE isn't really
much better).

IPython tries to:

  i - provide an efficient environment for interactive work in Python
  programming. It tries to address what we see as shortcomings of the standard
  Python prompt, and adds many features to make interactive work much more
  efficient.

  ii - offer a flexible framework so that it can be used as the base
  environment for other projects and problems where Python can be the
  underlying language. Specifically scientific environments like Mathematica,
  IDL and Mathcad inspired its design, but similar ideas can be useful in many
  fields. Python is a fabulous language for implementing this kind of system
  (due to its dynamic and introspective features), and with suitable libraries
  entire systems could be built leveraging Python's power.

  iii - serve as an embeddable, ready to go interpreter for your own programs.

IPython requires Python 2.1 or newer."""

# Define what gets imported with a 'from IPython import *'

__all__ = ('deep_reload genutils ultraTB DPyGetOpt Itpl ConfigLoader '
           'OutputTrap Release Struct Shell '.split() )

# Load __all__ in IPython namespace so that a simple 'import IPython' gives
# access to them via IPython.<name>
for name in __all__:
    __import__(name,globals(),locals(),[])

# Release data
import Release  # do it explicitly so pydoc can see it - pydoc bug
__version__ = Release.version
__date__    = Release.date
__author__  = '%s <%s>\n%s <%s>\n%s <%s>' % \
              ( Release.authors['Fernando'] + Release.authors['Janko'] + \
                Release.authors['Nathan'] )
__license__ = Release.license

# Namespace cleanup
del name
