"""
A set of convenient utilities for numerical work.

Most of this module requires Numerical Python or is meant to be used with it.
See http://www.pfdubois.com/numpy for details.
"""

#*****************************************************************************
#       Copyright (C) 2001 Fernando P�rez. <fperez@colorado.edu>
#
#  Distributed under the terms of the GNU Lesser General Public License (LGPL)
#
#    This code is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#  The full text of the LGPL is available at:
#
#                  http://www.gnu.org/copyleft/lesser.html
#*****************************************************************************

__author__ = 'Fernando P�rez. <fperez@colorado.edu>'
__version__= '0.1.1'
__license__ = 'LGPL'
__date__   = 'Tue Dec 11 00:27:58 MST 2001'

from genutils import qw
__all__ = qw('gnuplot_exec sum_flat mean_flat binary_repr zeros_like '
             'rms_flat frange diagonal_matrix fromfunction inf infty Infinity '
             'exp_safe spike spike_odd l2norm Numeric')

#****************************************************************************
# required modules
import math
import Numeric
from Numeric import *
import sys, ultraTB,operator
import __main__

try:
    import kinds
except ImportError:
    # Hand-built mockup of the things we need from the kinds package, since it
    # was recently removed from the standard Numeric distro.  Some users may
    # not have it by default, and we just need two things from it.
    class _bunch:
        pass
    
    class _kinds(_bunch):
        default_float_kind = _bunch()
        default_float_kind.MIN = 2.2250738585072014e-308
        default_float_kind.MAX = 1.7976931348623157e+308

    kinds = _kinds()

AutoTB = ultraTB.AutoFormattedTB(mode='Verbose',color_scheme='Linux')

#*****************************************************************************
# Globals

# useful for testing infinities in results of array divisions (which don't
# raise an exception)
# Python, LaTeX and Mathematica names.
inf = infty = Infinity = (array([1])/0.0)[0]

#****************************************************************************
# function definitions        
def exp_safe(x):
    """Compute exponentials which safely underflow to zero.

    Slow but convenient to use. Note that NumArray will introduce proper
    floating point exception handling with access to the underlying
    hardware."""

    if type(x) is not ArrayType:
        return math.exp(x)
    xmin = math.log(kinds.default_float_kind.MIN)
    xmax = kinds.default_float_kind.MAX
    return exp(clip(x,xmin,xmax))

def spike(x,x0=0,delta=1):
    """Return exp(-((x-x0)/delta)**2), a simple spike. """

    # for large arrays, the extra ifs are cheaper than the needless arithmetic
    if x0==0 and delta == 1:
        return exp_safe(-(x**2))
    elif x0==0:
        return exp_safe(-((x/delta)**2))
    elif delta == 1:
        return exp_safe(-(x-x0)**2)
    else:
        return exp_safe(-((x-x0)/delta)**2)

def spike_odd(x,x0=0,delta=1,norm = math.sqrt(2.0*math.e)):
    """Return (sqrt(2*E)/delta)*(x0-x)*exp(-((x-x0)/delta)**2).

    This is a simple odd spike normalized to amplitude 1 which starts
    positive."""

    if x0==0:
        return -(norm/delta)*x*spike(x,delta=delta)
    else:
        xnew = x0-x
        return (norm/delta)*xnew*spike(xnew,delta=delta)

def zeros_like(a):
    """Return an array of zeros of the shape and typecode of a."""

    return zeros(a.shape,a.typecode())
    
def sum_flat(a):
    """Return the sum of all the elements of a, flattened out (recursively)."""

    if type(a) is not ArrayType: return a
    return sum_flat(sum(a))

def mean_flat(a):
    """Return the mean of all the elements of a, flattened out (recursively)."""

    return sum_flat(a)/float(size(a))

def rms_flat(a):
    """Return the root mean square of all the elements of a, flattened out
    (recursively)."""

    return sqrt(sum_flat(absolute(a)**2)/float(size(a)))

def l2norm(a):
    """Return the l2 norm of a, flattened out (recursively)."""

    return sqrt(sum_flat(absolute(a)**2))
    
def frange(xini,xfin=None,delta=None,**kw):
    """frange([start,] stop[, step, keywords]) -> list of floats

    Return a Numeric array() containing a progression of floats. Similar to
    arange(), but defaults to a closed interval.

    frange(x0, x1) returns [x0, x0+1, x0+2, ..., x1]; start defaults to 0, and
    the endpoint *is included*. This behavior is different from that of
    range() and arange(). This is deliberate, since frange will probably be
    more useful for generating lists of points for function evaluation, and
    endpoints are often desired in this use. The usual behavior of range() can
    be obtained by setting the keyword 'closed=0', in this case frange()
    basically becomes arange().

    When step is given, it specifies the increment (or decrement). All
    arguments can be floating point numbers.

    frange(x0,x1,d) returns [x0,x0+d,x0+2d,...,xfin] where xfin<=x1.

    frange can also be called with the keyword 'npts'. This sets the number of
    points the list should contain (and overrides the value 'step' might have
    been given). arange() doesn't offer this option.

    Examples:
    >>> frange(3)
    array([ 0.,  1.,  2.,  3.])
    >>> frange(3,closed=0)
    array([ 0.,  1.,  2.])
    >>> frange(1,6,2)
    array([1, 3, 5])
    >>> frange(1,6.5,npts=5)
    array([ 1.   ,  2.375,  3.75 ,  5.125,  6.5  ])
    """

    #defaults
    kw.setdefault('closed',1)
    endpoint = kw['closed'] != 0
        
    # funny logic to allow the *first* argument to be optional (like range())
    # This was modified with a simpler version from a similar frange() found
    # at http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66472
    if xfin == None:
        xfin = xini + 0.0
        xini = 0.0
        
    if delta == None:
        delta = 1.0

    # compute # of points, spacing and return final list
    try:
        npts=kw['npts']
        delta=(xfin-xini)/float(npts-endpoint)
    except KeyError:
        npts=int((xfin-xini)/delta+endpoint)

    return arange(npts)*delta+xini
# end frange()

def diagonal_matrix(diag):
    """Return square diagonal matrix whose non-zero elements are given by the
    input array."""

    return diag*identity(len(diag))

def base_repr (number, base = 2, padding = 0):
    """Return the representation of a number in any given base."""
    chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    if number < base: \
       return (padding - 1) * chars [0] + chars [int (number)]
    max_exponent = int (math.log (number)/math.log (base))
    max_power = long (base) ** max_exponent
    lead_digit = int (number/max_power)
    return chars [lead_digit] + \
           base_repr (number - max_power * lead_digit, base, \
                      max (padding - 1, max_exponent))

def binary_repr(number, max_length = 1025):
    """Return the binary representation of the input number as a string.

    This is more efficient than using base_repr with base 2.

    Increase the value of max_length for very large numbers. Note that on
    32-bit machines, 2**1023 is the largest integer power of 2 which can be
    converted to a Python float."""
    
    assert number < 2L << max_length
    shifts = map (operator.rshift, max_length * [number], \
                  range (max_length - 1, -1, -1))
    digits = map (operator.mod, shifts, max_length * [2])
    if not digits.count (1): return 0
    digits = digits [digits.index (1):]
    return ''.join (map (repr, digits)).replace('L','')

def log2(x,ln2 = math.log(2.0)):
    """Return the log(x) in base 2.
    
    This is a _slow_ function but which is guaranteed to return the correct
    integer value if the input is an ineger exact power of 2."""

    try:
        bin_n = binary_repr(x)[1:]
    except (AssertionError,TypeError):
        return math.log(x)/ln2
    else:
        if '1' in bin_n:
            return math.log(x)/ln2
        else:
            return len(bin_n)

def ispower2(n):
    """Returns the log base 2 of n if n is a power of 2, zero otherwise.

    Note the potential ambiguity if n==1: 2**0==1, interpret accordingly."""
    bin_n = binary_repr(n)[1:]
    if '1' in bin_n:
        return 0
    else:
        return len(bin_n)

def fromfunction_kw(function, dimensions, **kwargs):
    """Drop-in replacement for fromfunction() from Numerical Python.
 
    Allows passing keyword arguments to the desired function.

    Call it as (keywords are optional):
    fromfunction_kw(MyFunction, dimensions, keywords)

    The function MyFunction() is responsible for handling the dictionary of
    keywords it will recieve."""

    return function(tuple(indices(dimensions)),**kwargs)


#-----------------------------------------------------------------------------
# DEPRECATED CODE

# gnuplot can already take multi-line strings, so this was unnecessary!
def gnuplot_exec(gnuplot,string_of_commands,verbose=0):
    """Have gnuplot execute a string of commands, one per line.

    DEPRECATED."""

    if verbose:
        print 'Calling gnuplot to execute:'
    for cmd in string_of_commands.splitlines():
        if verbose:
            print cmd
        gnuplot(cmd)
#**************************** end file <numutils.py> ************************
