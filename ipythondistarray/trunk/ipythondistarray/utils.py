

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

def factor_pairs(n):
    factors = []
    if n == 1:
        return []
    i = 2
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
