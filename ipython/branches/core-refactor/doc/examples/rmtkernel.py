#-------------------------------------------------------------------------------
# Core routines for computing properties of symmetric random matrices.
#-------------------------------------------------------------------------------

import numpy
ra = numpy.random
la = numpy.linalg

def GOE(N):
    """Creates an NxN element of the Gaussian Orthogonal Ensemble"""
    m = ra.standard_normal((N,N))
    m = m + numpy.transpose(m)
    return m


def centerEigenvalueDiff(mat):
    """Compute the eigvals of mat and then find the center eigval difference."""
    N = len(mat)
    evals = numpy.sort(la.eigvals(mat))
    diff = evals[N/2] - evals[N/2-1]
    return diff.real


def ensembleDiffs(num, N):
    """Return the a list of num eigenvalue differences for the NxN GOE ensemble."""
    diffs = numpy.empty(num)
    for i in xrange(num):
        mat = GOE(N)
        diffs[i] = centerEigenvalueDiff(mat)
    return diffs


def normalizeDiffs(diffs):
    """Normalize an array of eigenvalue diffs."""
    meanDiff = numpy.sum(diffs)/len(diffs)
    diffsNormalized = diffs/meanDiff
    return diffsNormalized


def normalizedEnsembleDiffs(num, N):
    """Return the a list of num eigenvalue differences for the NxN GOE ensemble."""
    diffs = ensembleDiffs(num, N)
    return normalizeDiffs(diffs)

