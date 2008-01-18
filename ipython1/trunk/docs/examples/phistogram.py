"""Parallel histogram function"""
import numpy

def phistogram(rc, a, bins=10, rng=None, normed=False):
    """Compute the histogram of a remote array a.
    
    :Parameters:
        rc
            IPython RemoteController instance
        a : str
            String name of the remote array
        bins : int
            Number of histogram bins
        rng : (float, float)
            Tuple of min, max of the range to histogram
        normed : boolean
            Should the histogram counts be normalized to 1
    """
    nengines = len(rc)
    rc.pushAll(bins=bins, rng=rng)
    rc.executeAll('import numpy')
    rc.executeAll('hist, lower_edges = numpy.histogram(%s, bins, rng)' % a)
    lower_edges = rc.pull(0, 'lower_edges')
    hist_array = rc.gatherAll('hist')
    hist_array.shape = (nengines,-1)
    total_hist = numpy.sum(hist_array, 0)
    if normed:
        total_hist = total_hist/numpy.sum(total_hist,dtype=float)
    return total_hist, lower_edges


    
    
