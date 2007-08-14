#!/usr/bin/env python
"""Parallel word frequency counter."""


from itertools import repeat
from wordfreq import print_wordfreq, wordfreq

def pwordfreq(rc, text):
    """Parallel word frequency counter.
    
    rc - An IPython RemoteController
    text - The name of a string on the engines to do the freq count on.
    """


if __name__ == '__main__':
    # Create a RemoteController
    import ipython1.kernel.api as kernel
    ipc = kernel.RemoteController(('127.0.0.1',10105))
    
    # Run the wordfreq script on the engines.
    ipc.runAll('wordfreq.py')

    # Run the serial version
    print "Serial word frequency count:"
    text = open('davinci.txt').read()
    freqs = wordfreq(text)
    print_wordfreq(freqs, 10)
    
    # The parallel version
    print "\nParallel word frequency count:"
    files = ['davinci%i.txt' % i for i in range(4)]
    ipc.scatterAll('textfile', files)
    ipc.executeAll('text = open(textfile[0]).read()')
    pfreqs = pwordfreq(ipc,'text')
    print_wordfreq(freqs)
