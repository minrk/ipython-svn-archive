from math import sqrt

def divisors(n):
    i = 2
    while i<n:
        if n % i == 0:
            yield i
        i += 1

def multi_for(iterables):
    if not iterables:
        yield ()
    else:
        for item in iterables[0]:
            for rest_tuple in multi_for(iterables[1:]):
                yield (item,) + rest_tuple

def create_factors(n, size=2):
    divs = list(divisors(n))
    factors = []
    for indices in multi_for( [xrange(p) for p in size*[len(divs)]] ):
        total = 1
        for i in indices:
            total = total*divs[i]
        if n == total:
            factor = [divs[i] for i in indices]
            factor.sort()
            if factor not in factors:
                factors.append(factor)
    return factors


def divs_minmax(n, dmin, dmax):
    """Find the divisors of n in the interval [dmin,dmax]."""
    i = dmin+1
    while i<=dmax:
        if n % i == 0:
            yield i
        i += 1

def cfactors(n, s, pd=0):
    if s == 2:
        print factor_pairs(n, pd+2)
        return
    divs = divs_minmax(n, pd+1, int(sqrt(n)))
    divs = list(divs)
    print "divs: ", divs
    for d in divs:
        print "cfactor for %s with s=%s, previous=%s:" % (n/d,s-1,pd)
        print cfactors(n/d, s-1, pd)
        pd = d
        


def mirror_sort(seq, ref_seq):
    """Sort s2 into the order that s1 is in."""
    assert len(seq)==len(ref_seq), "Sequences must have the same length"
    shift = zip(range(len(ref_seq)),ref_seq)
    shift.sort(key=lambda x:x[1])
    shift = [s[0] for s in shift]
    newseq = len(ref_seq)*[0]
    for s_index in range(len(shift)):
        newseq[shift[s_index]] = seq[s_index]
    return newseq

def factor_pairs(n, cutoff=2):
    factors = []
    if n == 1:
        return []
    i = cutoff
    while i<n:
        if n % i == 0:
            pair = [i,n/i]
            pair.sort()
            if pair not in factors:
                factors.append(pair)
        i += 1

    if factors==[]:
        return n
    else:
        return factors

def factor(n): 
    d = 2 
    factors = [ ] 
    while n >= d*d: 
        if n % d == 0:
            n = n/d
            factors.append((d,n)) 
        else: 
            d = d + 1 
    if n > 1: 
        factors.append(n) 
    return factors
