# -*- test-case-name: ipython1.test.test_controllerclient -*-
"""The kernel interface.

The kernel interface is a set of classes that providse a high level interface
to a running ipython kernel instance.  Currently these classes use blocking
sockets, and thus, do not require Twisted.

TODOs:
- Organize methods of RemoteController, RemoteControllerView and EngineProxy in 
  a consistent and logical manner.
- Check to make sure that RemoteControllerView and EngineProxy implement all the 
  methods they should.
- What should happen if the target given is an integer, but is not valid?
"""
#-------------------------------------------------------------------------------
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import ipython1.kernel.magic

class RemoteControllerBase(object):
    """The base class for all RemoteController objects.
    
    This calss is meant to provide capabilities that are independent of the
    network protocol used to implement the RemoteController, like testing
    facilities.
    
    It is important to note, that as of now, this is only designed to be
    used with network protocols that use standard non-blocking socket and not
    Twisted.  Such protocols are provided so that standard Python session
    can talk to Controllers.
    
    It is also designed to provide an informal client interface.  It is 
    informal as clients won't necessarily have Twisted or zope.interface
    installed.  The client interface is very similar, but not identical to 
    the IMultiEngine interface.
    
    Methods that should be implemented by subclasses:
    
     * execute
     * executeAll
     * push
     * pushAll
     * pull
     * pullAll
     * pullNamespace
     * pullNamespaceAll
     * getResult
     * getResultAll
     * reset
     * resetAll
     * status
     * statusAll
     * kill
     * killAll
     * pushSerialized (why not pullSerialized?)
     * getIDs
     * scatter
     * scatterAll
     * gather
     * gatherAll
     * notify (why not call addNotifier/delNotifier?  We should just make a clientAPI!)
     
     * activate     
     * run
     * runAll
     * __setitem__
     * __getitem__
     * map/reduce
     * vectorize?
     
     Some methods don't always make sense on RemoteControllerViews:
     
     * pushModule
     * connect
     * disconnect
     
    I can't declare these as pass methods in this base class, because some
    subclasses might generate the methods dynamically if they don't exist.  An
    examples of this are the fooAll() methods which are typically done
    dynamically.     
    """

    #---------------------------------------------------------------------------
    # Testing and timing methods
    #---------------------------------------------------------------------------

    def test(self, level):
        """Test a RemoteController Object"""
           
class RemoteControllerView(RemoteControllerBase):
    """A subset interface for RemoteController.__getitem__"""
    def __init__(self, rc, ids):
        self.rc = rc
        if isinstance(ids, slice):
            self._originalIDs = range(*ids.indices(ids.stop))
        elif isinstance(ids, list):
            self._originalIDs = ids
        else:
            raise TypeError("RemoteControllerView requires slice or list")
        # Make sure these exist as of now
        currentIDs = rc.getIDs()
        for id in self._originalIDs:
            if id not in currentIDs:
                raise Exception("The engine with id %i does not exist" % id)
        self._ids = range(len(self._originalIDs))
        # print self._ids
        # print self._originalIDs
    
    #---------------------------------------------------------------------------
    # RemoteController methods
    #---------------------------------------------------------------------------
    
    def execute(self, targets, lines, block=False):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.execute(actualTargets, lines, block)
    
    def executeAll(self, lines, block=False):
        return self.execute('all', lines, block)
        
    def push(self, targets, **namespace):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.push(actualTargets, **namespace)
    
    def pushAll(self, **namespace):
        return self.push('all', **namespace)
        
    def pull(self, targets, *keys):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.pull(actualTargets, *keys)
    
    def pullAll(self, *keys):
        r = self.pull('all', *keys)
        if len(self._ids) is 1:
            r = [r]
        return r
        
    def pullNamespace(self, targets, *keys):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.pullNamespace(actualTargets, *keys)
    
    def pullNamespaceAll(self, *keys):
        return self.pullNamespace('all', *keys)
        
    def getResult(self, targets, i=None):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.getResult(actualTargets, i)
    
    def getResultAll(self, i=None):
        r = self.getResult('all', i)
        if len(self._ids) is 1:
            r = [r]
        return r
        
    def reset(self, targets):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.reset(actualTargets)
    
    def resetAll(self):
        return self.reset('all')

    def status(self, targets):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.status(actualTargets)
    
    def statusAll(self):
        r = self.status('all')
        if len(self._ids) is 1:
            r = [r]
        return r
        
    def kill(self, targets):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.kill(actualTargets)
    
    def killAll(self):
        return self.kill('all')
        
    def pushSerialized():
        pass
        
    def getIDs(self):
        return self._originalIDs

    def scatter(self, targets, key, seq, style='basic', flatten=False):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.scatter(actualTargets, key, seq, style, flatten)
    
    def scatterAll(self, key, seq, style='basic', flatten=False):
        return self.scatter('all', key, seq, style, flatten)
        
    def gather(self, targets, key, style='basic'):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.gather(actualTargets, key, style)        
    
    def gatherAll(self, key, style='basic'):
        return self.gather('all', key, style)
        
    def notify(self, addr=None, flag=True):
        self.rc.notify(addr, flag)
        
    def activate(self):
        try:
            __IPYTHON__.active_cluster = self
        except NameError:
            print "The %px and %autopx magic's are not active."
        
    def run(self, targets, fname):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.run(actualTargets, fname)
    
    def runAll(self, fname):
        return self.run('all', fname)
        
    def __setitem__(self, key, value):
        return self.push('all', **{key:value})
            
    def __getitem__(self, id):
        if isinstance(id, slice):
            return RemoteControllerView(self.rc, self._originalIDs[id])
        elif isinstance(id, int):
            return EngineProxy(self.rc, self._originalIDs[id])
        elif isinstance(id, str):
            return self.pull('all',*(id,))
        else:
            raise TypeError("__getitem__ only takes strs, ints, and slices")
        
    #---------------------------------------------------------------------------
    # Methods specific to a RemoteControllerView
    #---------------------------------------------------------------------------
        
    def getMappedIDs(self):
        return self._ids
        
    def _mapIDsToOriginal(self, ids):
        if ids == 'all':
            return self._originalIDs
        elif isinstance(ids, int) and ids in self._ids:
            return self._originalIDs[ids]
        elif isinstance(ids, (list, tuple)):
            return [self._originalIDs[i] for i in ids]
        else:
            raise TypeError("targets/ids must be int, list or tuple")
    
class EngineProxy(object):
    """A proxy for an Engine that goes through a RemoteController.

    The user won't ever create these directly.  Instead, the actual
    RemoteController class does that when a particular Engine is indexed.
    """

    def __init__(self, rc, id):
        self.id = id
        self.rc = rc
    
    def execute(self, strings, block=False):
        if block:
            return self.rc.execute(self.id, strings, block=True)[0]
        else:
            return self.rc.execute(self.id, strings)
    
    def push(self, **namespace):
        return self.rc.push(self.id, **namespace)
    
    def pull(self, *keys):
        return self.rc.pull(self.id, *keys)
    
    def pullNamespace(self, *keys):
        return self.rc.pullNamespace(self.id, *keys)

    def getResult(self, i=None):
        return self.rc.getResult(self.id, i)
    
    def status(self):
        return self.rc.status(self.id)
    
    def reset(self):
        return self.rc.reset(self.id)
    
    def kill(self):
        return self.rc.kill(self.id)

    def __setitem__(self, key, value):
        return self.push(**{key:value})
        
    def __getitem__(self, key):
        return self.pull(*(key,))
