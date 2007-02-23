# encoding: utf-8
"""Make Twisted Deferred objects look synchronous.

Yes, I know that the premise of this module is considered heresy by the
Twisted cool-aid drinkers.  Nonetheless, it is still useful.

>>> d = functionThatReturnsDeferred()
>>> blockOn(d)
10

If the Deferred's errback is called, an exception is raised.

blockOn() also can take multiple Deferred's and will return a list of 
results:

>>> blockOn(d0, d1, d2)
['wow', 'really', 'cool']

IMPORTANT:  Before you exit the Python interpreter, you must call the
stopReactor() function.  This shuts down the Twisted reactor.

IMPORTANT:  The startReactor() function is called automatically upon
importing this module, so you don't have to.
"""

from twisted.internet import reactor
from twisted.python import failure
from twisted.internet import defer

TIMEOUT = 0.05                  # Set the timeout for poll/select

class BlockingDeferred(object):
    """Wrap a Deferred into a blocking API."""
    
    def __init__(self, d):
        """Wrap a Deferred d."""
        self.d = d
        self.finished = False
        self.count = 0

    def blockOn(self):
        """Call this to block and get the result of the wrapped Deferred.
        
        On success this will return the result.
        
        On failure, it will raise an exception.
        """
        
        self.d.addBoth(self.gotResult)
        while not self.finished:
            reactor.iterate(TIMEOUT)
            self.count += 1
        if isinstance(self.d.result, failure.Failure):
            self.d.result.raiseException()
        else:
            return self.d.result

    def gotResult(self, result):
        self.finished = True
        return result
        
def _parseResults(resultList):
    newResult = [r[1] for r in resultList]
    if len(newResult) == 1:
        return newResult[0]
    else:
        return newResult
        
def blockOn(*deferredList):
    """Make a Deferred look synchronous.
    
    Given a Deferred object, this will run the Twisted event look until
    the Deferred's callback and errback chains have run.  It will then 
    return the actual result or raise an exception if an error occured.
    
    >>> blockOn(functionReturningDeferred())
    10
    
    You can also pass multiple Deferred's to this function and you will
    get a list of results.
    
    >>> blockOn(d0, d1, d2)
    ['this', 'is', 'heresy']
    """
    
    d = defer.DeferredList(deferredList, consumeErrors=True)
    d.addCallback(_parseResults)
    bd = BlockingDeferred(d)
    return bd.blockOn()
    
def startReactor():
    """Initialize the twisted reactor, but don't start its main loop."""
    if not reactor.running:
        reactor.startRunning()
    
def stopReactor():
    """Stop the twisted reactor when its main loop isn't running."""
    if reactor.running:
        reactor.callLater(0, reactor.stop)
        while reactor.running:
            reactor.iterate(TIMEOUT)
    
startReactor()

# This was running when a %run blockon.py was done from IPython.
# The problem is that stopReactor() was being called which killed it.
if __name__ == '__main__':
    from twisted.web import client
    startReactor()
    d = client.getPage('http://www.google.com/')
    print blockOn(d)
    stopReactor()
