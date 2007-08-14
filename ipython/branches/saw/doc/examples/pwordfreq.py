#!/usr/bin/env python
"""Parallel word frequency counter."""


from itertools import repeat
from wordfreq import print_wordfreq, wordfreq

def pwordfreq(rc, text):
    rc.executeAll('freqs = wordfreq(%s)' %text)
    freqs_list = rc.pullAll('freqs')
    word_set = set()
    for f in freqs_list:
        word_set.update(f.keys())
    freqs = dict(zip(word_set, repeat(0)))
    for f in freqs_list:
        for word, count in f.iteritems():
            freqs[word] += count
    return freqs

if __name__ == '__main__':
    import ipython1.kernel.api as kernel
    ipc = kernel.RemoteController(('127.0.0.1',10105))
    
    ipc.runAll('wordfreq.py')
    ipc.executeAll('import gzip')
    ipc.executeAll('text = gzip.open("HISTORY.gz").read()')
    freqs = pwordfreq(ipc,'text')
    print_wordfreq(freqs)
