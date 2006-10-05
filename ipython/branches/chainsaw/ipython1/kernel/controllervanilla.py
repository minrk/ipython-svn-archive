"""A vanilla protocol interface to a `ControllerService`.

The client side of this uses standard blocking Python sockets and can 
be used from an interactive Python session.

The server side is written as a Twisted protocol/factory and follows the 
adapter/interface design pattern of the other client protocols.

To do:

- `IVanillaControllerFactory` is missing lots of method that are implemented
  in `VanillaControllerFactoryFromService`.  I now understand why the fooAll 
  methods and push/pull aren't there, but what about the other methods?
- `VanillaControllerFactoryFromService` implements `addNotifier` and `delnotifier`, 
  but these methods are not in the `IVanillaControllerFactory` interface or
  anywhere in the `ControllerService` interface or implementation.

"""
__docformat__ = "restructuredtext en"
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

import socket, cPickle as pickle

from twisted.internet import defer
from twisted.internet.interfaces import IProducer
from twisted.python import components, log
from twisted.python.failure import Failure
from zope.interface import Interface, implements

from IPython.ColorANSI import TermColors

import ipython1.kernel.magic
from ipython1.kernel import controllerservice, serialized, protocols, results
from ipython1.kernel.util import tarModule
from ipython1.kernel.controllerclient import \
    RemoteControllerBase, RemoteControllerView, EngineProxy
from ipython1.kernel.parallelfunction import ParallelFunction


#-------------------------------------------------------------------------------
# Figure out what array packages are present and their types.
#-------------------------------------------------------------------------------

arraytypeList = []
try:
    import Numeric
except ImportError:
    pass
else:
    arraytypeList.append(Numeric.arraytype)
try:
    import numpy
except ImportError:
    pass
else:
    arraytypeList.append(numpy.ndarray)
try:
    import numarray
except ImportError:
    pass
else:
    arraytypeList.append(numarray.numarraycore.NumArray)

arraytypes = tuple(arraytypeList)
del arraytypeList


#-------------------------------------------------------------------------------
# The client side of things
#-------------------------------------------------------------------------------

class RemoteController(RemoteControllerBase):
    """A high level interface to a remotely running IPython controller."""
    
    MAX_LENGTH = 99999999
    
    def __init__(self, addr):
        """Create a `RemoteController` instance pointed at a specific controller.
        
        :arg addr:  The (ip,port) tuple of the kernel, like ('192.168.0.1',10000)
        """
        self.addr = addr
        self.block = True
        controllerservice.addAllMethods(self)
        self.activate()
    
    #-------------------------------------------------------------------------------
    # Internal implementation methods
    #-------------------------------------------------------------------------------

    def __del__(self):
        """Disconnect upon being deleted."""
        
        return self.disconnect()
    
    def isConnected(self):
        """Are we connected to the controller?
        
        :return: True or False.
        """ 
        
        if hasattr(self, 's'):
            try:
                self.s.send('')
            except socket.error:
                return False
            else:
                return True
    
    def _checkConnection(self):
        """Reconnect if we are not connected to the controller."""
        
        if not self.isConnected():
            return self.connect()
        return True

    def _parseTargets(self, targets):
        """Parse and validate the targets argument."""
        
        if isinstance(targets, int):
            if targets >= 0:
                return str(targets)
        elif isinstance(targets, (list, tuple)):
            if not targets:
                return False
            for t in targets:
                if not isinstance(t, int) or t < 0:
                    return False
            return '::'.join(map(str, targets))
        elif targets == 'all':
            return targets
        return False
    
    def _multiTargets(self, targets):
        """Are we dealing with multiple targets?"""
        
        return not isinstance(targets, int) and len(targets) > 1
    
    def _pushModuleString(self, tarballName, fileString):
        """Send a tarballed module to all engines.
        
        :Parameters:
        - `tarballName`: The filename of the tarball as a string.
        - `fileString`: The tarballed file as a string.
        """
        
        self.pushAll(tar_fileString=fileString)
        self.executeAll("tar_file = open('%s','wb')" % \
            tarball_name, block=False)
        self.executeAll("tar_file.write(tar_fileString)", block=False)
        self.executeAll("tar_file.close()", block=False)
        self.executeAll("import os", block=False)
        self.executeAll("os.system('tar -xf %s')" % tarballName)        
    
    def _sendSerialized(self, serial):
        assert isinstance(serial, serialized.Serialized)
        for line in serial:
            self.es.writeNetstring(line)
    
    #-------------------------------------------------------------------------------
    # IMultiEngine methods
    #-------------------------------------------------------------------------------
        
    def execute(self, targets, source, block=False):
        """Execute python source code on engine(s).
        
        Examples:
        
        >>> rc = RemoteController(('localhost',10000))
        >>> rc.execute('all', a=5)
        >>> rc.execute(0, 'import math')
        >>> rc.execute(range(0,10,2) 'print a', block=True)
        
        There is also a magic command interface for executing commands in IPython.
        See `activate` for more information.
        
        :Parameters:
         - `targets`: The engine id(s) on which to execute. Targets can be an int, 
           list of ints, or the string 'all' to indicate all available engines.  
           To see the current ids available on a controller use `getIDs()`.
         - `source`: A string containing valid python code.
         - `block`:  Whether or not to wait for the results of the action.  Using 
           ``block=True`` will wait for results, which will be printed as 
           stdin/out/err.  Using ``block=False`` will submit the action to the 
           controller and return immediately. Blocking can also be controlled on a
           global basis by setting the ``block`` attribute of the `RemoteController` 
           object.
            
        :return: ``True`` or ``False`` to indicate success or failure.
        """
        
        targetstr = self._parseTargets(targets)
        if not targetstr or not source:
            print "Need something to do!"
            return False
        self._checkConnection()
        
        if self.block or block:
            string = "EXECUTE BLOCK %s::%s" % (source, targetstr)
            try:
                self.es.writeNetstring(string)
            except socket.error:
                try:
                    self.connect()
                    self.es.writeNetstring(string)
                except socket.error:
                    print "Not Connected"
                    return False
            string = self.es.readNetstring()
            if string [:3] == 'BAD':
                print string
                return False
            data = []
            while string not in ['EXECUTE FAIL', "EXECUTE OK"]:
                package = self.es.readNetstring()
                if string in ["PICKLE RESULT", "PICKLE FAILURE"]:
                    try:
                        data.append(pickle.loads(package))
                    except pickle.PickleError, e:
                        print "Error unpickling object: ", e
                        return False
                else:
                    print "Expected pickle, received ", string
                    return False
                string = self.es.readNetstring()
                
            # Now print data
            blue = TermColors.Blue
            normal = TermColors.Normal
            red = TermColors.Red
            green = TermColors.Green
            for cmd in data:
                if isinstance(cmd, Failure):
                    print cmd
                else:
                    target = cmd[0]
                    cmd_num = cmd[1]
                    cmd_stdin = cmd[2]
                    cmd_stdout = cmd[3][:-1]
                    cmd_stderr = cmd[4][:-1]
                    print "%s[%s:%i]%s In [%i]:%s %s" % \
                        (green, self.addr[0], target,
                        blue, cmd_num, normal, cmd_stdin)
                    if cmd_stdout:
                        print "%s[%s:%i]%s Out[%i]:%s %s" % \
                            (green, self.addr[0], target,
                            red, cmd_num, normal, cmd_stdout)
                    if cmd_stderr:
                        print "%s[%s:%i]%s Err[%i]:\n%s %s" % \
                            (green, self.addr[0], target,
                            red, cmd_num, normal, cmd_stderr)
        else:
            string = "EXECUTE %s::%s" % (source, targetstr)
            try:
                self.es.writeNetstring(string)
            except socket.error:
                try:
                    self.connect()
                    self.es.writeNetstring(string)
                except socket.error:
                    print "Not Connected"
                    return False
            string = self.es.readNetstring()
            data = None
             
        if string == "EXECUTE OK":
            return True
        else:
            print string
            return False

    def executeAll(self, source, block=False):
        """Execute source on all engines.
        
        See the docstring for `execute` for more details.
        """
        return self.execute('all', source, block)

    def push(self, targets, **namespace):
        """Send python object(s) to remote engine(s).
        
        This should be able to send any picklable Python object.  Any modules 
        referenced in the object will need to be available on the engines.
        Also, Numpy arrays are sent without pickling using their buffers.
        
        Examples:
        
        >>> rc = RemoteController(('localhost',10000))
        >>> rc.push('all', a=5, b=10)      # push 5 as a, 10 as b to all
        >>> rc.push(0, c=range(10))        # push range(10) as c to 0
        >>> rc.push([0,3], q='mystring')   # push 'mystring' as q to 0, 3
        
        There is also a dictionary style interface to the push command:
                
        >>> rc['a'] = 10                   # Same as rc.push('all', a=10)
        >>> rc[0]['b'] = 30                # Same as rc.push(0, b=30)
        
        :Parameters:
         - `targets`: The engine id(s) to push to. Targets can be an int, 
           list of ints, or the string 'all' to indicate all available engines.  
           To see the current ids available on a controller use `getIDs()`.
         - `**namespace`:  The python objects to send and their names represented as
           keyword arguments: a=10, b=20.
          
        :return: ``True`` or ``False`` to indicate success or failure.
        """
        
        targetstr = self._parseTargets(targets)
        if not targetstr or not namespace or not self._checkConnection():
            print "Need something to do!"
            return False
        
        string = "PUSH ::%s" % targetstr
        try:
            self.es.writeNetstring(string)
        except socket.error:
            try:
                self.connect()
                self.es.writeNetstring(string)
            except socket.error:
                print "Not Connected"
                return False
        string = self.es.readNetstring()
        if string != "PUSH READY":
            print "Expected 'PUSH READY', got '%s'" %string
            return False
        for key in namespace:
            value = namespace[key]
            try:
                serialObject = serialized.serialize(value, key)
            except Exception, e:
                print "Object cannot be serialized: ", key, e
                return False
            else:
                self._sendSerialized(serialObject)
        self.es.writeNetstring("PUSH DONE")
        string = self.es.readNetstring()
        if string == "PUSH OK":
            return True
        elif string == "PUSH FAIL":
            print "Push Failed"
            return False
        else:
            return string

    def pushAll(self, **namespace):
        """Push python objects to all engines.
        
        See the docstring for `push` for more details.
        """
        return self.push('all', **namespace)
        
    def pull(self, targets, *keys):
        """Get python object(s) from remote engines(s).
                
        The object must be pickable.  If the object does not exist in the 
        engines's namespace a NotDefined object will be returned.
        
        Examples:
        
        >>> rc = RemoteController(('localhost',10000))
        >>> rc.pushAll(a=5,b=10)
        >>> rc.pull(0,'a','b')
        (5, 10)
        
        Like push, pull also has a dictionary interface:

        >>> rc['a'] = 10       # Same as rc.push('all', a=10)
        >>> rc[0]['a']         # Same as rc.pull(0,'a')
        10
        
        :Parameters:
         - `targets`: The engine id(s) to pull from. Targets can be an int, 
           list of ints, or the string 'all' to indicate all available engines.  
           To see the current ids available on a controller use `getIDs()`.
         - `*keys`: The name of the python objects to pull as positional 
           arguments, like 'a', 'b', 'c'.

        :return:  There are four cases depending on the number of keys and 
            targets: i) (1 target, 1 key) the value of key on target, ii) 
            (1 target, >1 keys) a list of the values of keys on target, iii) 
            (>1 target, 1 key) a tuple of the values of key on targets and iv)
            (>1 targets, >1 keys) a list of length(keys) of tuples of len(targets).
        """
        targetstr = self._parseTargets(targets)
        if not targetstr or not keys or not self._checkConnection():
            print "Need something to do!"
            return False
        
        try:
            keystr = ','.join(keys)
        except TypeError:
            print "keys must be strings"
            return False
        
        multitargets = self._multiTargets(targets)
        string = "PULL %s::%s" % (keystr, targetstr)
        try:
            self.es.writeNetstring(string)
        except socket.error:
            try:
                self.connect()
                self.es.writeNetstring(string)
            except socket.error:
                print "Not Connected"
                return False
        
        string = self.es.readNetstring()
        if string [:3] == 'BAD':
            print string
            return False
        results = []
        returns = []
        while string not in ['PULL OK', 'PULL FAIL']:
            string_split = string.split(' ', 1)
            if len(string_split) is not 2:
                print "Pull Failed, invalid line: "+string
                return False
            if string_split[0] == "PICKLE":
                # if it's a pickle
                sPickle = serialized.PickleSerialized(string_split[1])
                sPickle.addToPackage(self.es.readNetstring())
                try:
                    data = sPickle.unpack()
                except pickle.PickleError, e:
                    print "Error unpickling object: ", e
                    return False
            elif string_split[0] == 'ARRAY':
                #if it's an array
                try:
                    sArray = serialized.ArraySerialized(string_split[1])
                except NameError:
                    print "Could not serialize"
                    return False    
                for i in range(3):#arrays have a 3 line package
                    sArray.addToPackage(self.es.readNetstring())
                data = sArray.unpack()
            else:
                #we don't know how to handle it!
                print "'%s' is not a valid serialized handle" %string
                return False
            
            #successful retrieval
            results.append(data)
            #get next string and reenter loop
            string = self.es.readNetstring()
            if string == "SEGMENT PULLED":
                if len(results) is 1:
                    results = results[0]
                returns.append(results)
                results = []
                string = self.es.readNetstring()
        #finish pulling
        if not returns:
            #if it was not a nested list
            returns = [results]
        if string == 'PULL OK':
            if not multitargets:
                returns = returns[0]
            elif len(keys) > 1:
                returns = zip(*returns)
            elif len(keys) is 1:
                returns = tuple(returns)
            return returns
        else:
            print string
            return False

    def pullAll(self, *keys):
        """Pull objects specified by keys from all engines.
        
        See the docstring for `pull` for more details.
        """
        return self.pull('all', *keys)
        
    def pullNamespace(self, targets, *keys):
        """Like `pull`, but returns a dict of key, value pairs.
        
        :Parameters:
         - `targets`: The engine id(s) to pull from. Targets can be an int, 
           list of ints, or the string 'all' to indicate all available engines.  
           To see the current ids available on a controller use `getIDs()`.
         - `*keys`: The name of the python objects to pull as positional 
           arguments, like 'a', 'b', 'c'.
        
        :return:  For 1 target, returns a dict of key value pairs.  For >1
            targets, a list of dicts of key, value pairs.
        """
        
        targetstr = self._parseTargets(targets)
        if not targetstr or not keys or not self._checkConnection():
            print "Need something to do!"
            return False
        
        multitargets = self._multiTargets(targets)
        values = self.pull(targets, *keys)
        if values == False:
            # could be bad, but not *necessarily*
            if multitargets or len(keys) > 1:
                # definitely bad
                return False
            elif not self.execute(targets, ' '):
                # check bad target failure
                # probably do not want to do this 
                return False
        
        if len(keys) > 1 and multitargets:
            results = zip(*values)
        elif multitargets:
            results = values
        elif len(keys) > 1:
            results = [values]
        else:
            dikt = {}
            dikt[keys[0]] = values
            return dikt
        returns = []
        for r in results:
            dikt = {}
            if len(keys) == 1:
                kv = ((keys[0], r),)
            else:
                kv = zip(keys, r)
            for k,v in kv:
                dikt[k] = v
            returns.append(dikt)
        if not multitargets:
            returns = returns[0]
        return returns
            
    def pullNamespaceAll(self, *keys):
        """`pullNamespace` on all engines.
        
        See the docstring for `pullNamespace` for more details.
        """
        return self.pullNamespace('all', *keys)
            
    def getResult(self, targets, i=None):
        """Gets a result (#, stdin, stdout, stderr) from engine(s).
        
        :Parameters:
         - `targets`: The engine id(s) to get the result from. Targets can be 
           an int, list of ints, or the string 'all' to indicate all 
           available engines.  To see the current ids available on a 
           controller use `getIDs()`.        
         - `i`: The result number to get.  If ``None``, the most recent result.
        :return:  A tuple of (#, stdin, stdout, stderr) for each target.
        """
        
        targetstr = self._parseTargets(targets)
        if not targetstr or not self._checkConnection():
            print "Need something to do!"
            return False
        
        if i is None:
            string = "GETRESULT ::%s" %targetstr
        else:
            string = "GETRESULT %i::%s" % (i, targetstr)
        try:
            self.es.writeNetstring(string)
        except socket.error:
            try:
                self.connect()
                self.es.writeNetstring(string)
            except socket.error:
                print "Not Connected"
                return False
        
        string = self.es.readNetstring()
        if string == "PICKLE RESULT":
            package = self.es.readNetstring()
            string = self.es.readNetstring()
            try:
                data = pickle.loads(package)
            except pickle.PickleError, e:
                print "Error unpickling object: ", e
                return False
            else:
                if string == "GETRESULT OK":
                    if not self._multiTargets(targets):
                        data = data[0]
                    return data
                else:
                    print string
                    return False
        else:
            # For other data types
            print string
            return False
    
    def getResultAll(self, i=None):
        """Get result ``i`` from all engines.
        
        See the docstring for `getResult` for more details.
        """
        return self.getResult('all', i)
    
    def status(self, targets):
        """Check the status of the controller and engines.
        
        We have not yet settled on exaclty what information this method
        should return.  The particulars of this may change in the future.
        
        :Parameters:
         - `targets`: The engine id(s) to get the status from. Targets can be 
           an int, list of ints, or the string 'all' to indicate all 
           available engines.  To see the current ids available on a 
           controller use `getIDs()`.
        """
        
        targetstr = self._parseTargets(targets)
        if not targetstr or not self._checkConnection():
            print "Need something to do!"
            return False
        
        string = "STATUS ::%s" %targetstr
        try:
            self.es.writeNetstring(string)
        except socket.error:
            try:
                self.connect()
                self.es.writeNetstring(string)
            except socket.error:
                print "Not Connected"
                return False
        
        string = self.es.readNetstring()
        if string == "PICKLE STATUS":
            package = self.es.readNetstring()
            string = self.es.readNetstring()
            try:
                data = pickle.loads(package)
            except pickle.PickleError, e:
                print "Error unpickling object: ", e
                return False
            else:
                if string == "STATUS OK":
                    if not self._multiTargets(targets):
                        data = data[0][1]
                    return data
                else:
                    print string
                    return False
        else:
            print "Could not handle: "+string
            return False
    
    def statusAll(self):
        """Get the status of the controller and all engines.
        
        See the docstring for `status` for more details.
        """
        return self.status('all')
    
    def reset(self, targets):
        """Clear the users namespace on the engine(s).
        
        This tries to give the user a clean slate on an engine.  But
        any modules that have been imported will remain in memory, so doing
        a `reset` and then an ``import foo`` will not cause the ``foo`` to
        be reloaded.
        
        :Parameters:
         - `targets`: The engine id(s) to reset. Targets can be 
           an int, list of ints, or the string 'all' to indicate all 
           available engines.  To see the current ids available on a 
           controller use `getIDs()`.
           
        :return: ``True`` or ``False`` to indicate success or failure. 
        """
        
        targetstr = self._parseTargets(targets)
        if not targetstr or not self._checkConnection():
            print "Need something to do!"
            return False
        
        string = "RESET ::%s" %targetstr
        try:
            self.es.writeNetstring(string)
        except socket.error:
            try:
                self.connect()
                self.es.writeNetstring(string)
            except socket.error:
                print "Not Connected"
                return False
        
        string = self.es.readNetstring()
        if string == "RESET OK":
            return True
        else:
            print string
            return False      
    
    def resetAll(self):
        """Clear the users's namespace on all engines.
        
        See the docstring for `reset` for more details.
        """
        return self.reset('all')
    
    def kill(self, targets):
        """Kill the engine completely by stopping their reactors.
        
        This method kills the engines specified by targets by stopping
        their reactors.  For this to succeed, the engines must be in a state
        in which they can be reached.  Thus, if they have hung, this may not
        work.
        
        :Parameters:
         - `targets`: The engine id(s) to kill. Targets can be 
           an int, list of ints, or the string 'all' to indicate all 
           available engines.  To see the current ids available on a 
           controller use `getIDs()`.
           
        :return: ``True`` or ``False`` to indicate success or failure.
        """
        
        targetstr = self._parseTargets(targets)
        if not targetstr or not self._checkConnection():
            print "Need something to do!"
            return False
        string = "KILL ::%s" %targetstr
        try:
            self.es.writeNetstring(string)
        except socket.error:
            try:
                self.connect()
                self.es.writeNetstring(string)
            except socket.error:
                print "Not Connected"
                return False
        string = self.es.readNetstring()
        if string == "KILL OK":
            return True
        else:
            print string
            return False     
                
    def killAll(self):
        """Kill all active engines."""
        return self.kill('all')
                
    def getIDs(self):
        """Return the id list of the currently connected engines."""
        
        if not self._checkConnection():
            print "Not Connected"
            return False
        
        string = "GETIDS"
        try:
            self.es.writeNetstring(string)
        except socket.error:
            try:
                self.connect()
                self.es.writeNetstring(string)
            except socket.error:
                print "Not Connected"
                return False
        
        package = self.es.readNetstring()
        try:
            ids = pickle.loads(package)
        except pickle.PickleError:
            print "Could not build idlist"
            return False
        
        s = self.es.readNetstring()
        if s == "GETIDS OK":
            return ids
        else:
            print s
            return False
    
    getMappedIDs = getIDs
    
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        """Partition and distribute a sequence of objects to engines.
        
        Examples:
        
        Fill in examples!
        
        :Parameters:
         - `targets`: The engine id(s) to scatter to. Targets can be 
           an int, list of ints, or the string 'all' to indicate all 
           available engines.  To see the current ids available on a 
           controller use `getIDs()`.
         - `key': What to call the scattered partitions.
         - `seq`: The list, tuple or array to scatter.
         - `style`: A string to determine how the sequence is scattered.
           Currently only 'basic' is supported.
         - `flatten`: A boolean flag to determine if partitions of lenth
           1 are scattered as scalars.  Defaults to ``False``.
           
        :return: ``True`` or ``False`` to indicate success or failure.   
        """
        
        targetstr = self._parseTargets(targets)
        if not targetstr or not key or not self._checkConnection()\
                or not isinstance(seq, (tuple, list)+arraytypes) \
                or not len(seq) > 0:
            print "Need something to do"
            return False
        
        try:
            serial = serialized.serialize(seq, key)
        except:
            print "Could not serialize "+key
            return False
        string = 'SCATTER style=%s flatten=%i::%s' %(
                        style, int(flatten), targetstr)
        try:
            self.es.writeNetstring(string)
        except socket.error:
            try:
                self.connect()
                self.es.writeNetstring(string)
            except socket.error:
                print "Not Connected"
                return False
        
        self._sendSerialized(serial)
        reply = self.es.readNetstring()
        if reply == 'SCATTER OK':
            return True
        else:
            print reply
            return False
    
    def scatterAll(self, key, seq, style='basic', flatten=False):
        """Scatter sequence to all engines.
        
        See the docstring for `scatter` for more details.
        """
        return self.scatter('all', key, seq, style=style, flatten=flatten)
    
    def gather(self, targets, key, style='basic'):
        """Gather a objects, and assemble them into a list.
        
        :Parameters:
         - `targets`: The engine id(s) to gather from. Targets can be 
           an int, list of ints, or the string 'all' to indicate all 
           available engines.  To see the current ids available on a 
           controller use `getIDs()`.
         - `key': The name of the object to gather.
         - `style`: A string to determine how the sequence is gathered.
           Currently only 'basic' is supported.
           
        :return:  Flattened list or array of objects. 
        """
        
        targetstr = self._parseTargets(targets)
        if not targetstr or not key or not self._checkConnection():
            print "Need something to do!"
            return False
        
        string = 'GATHER %s style=%s::%s' %(key, style, targetstr)
        try:
            self.es.writeNetstring(string)
        except socket.error:
            try:
                self.connect()
                self.es.writeNetstring(string)
            except socket.error:
                print "Not Connected"
                return False
        
        split = self.es.readNetstring().split(' ',1)
        if len(split) is not 2:
            print "Bad response: "+split[0]
            return False
        if split[0] == 'PICKLE':
            serial = serialized.PickleSerialized(key)
            serial.addToPackage(self.es.readNetstring())
            try:
                obj = serial.unpack()
            except pickle.PickleError, e:
                print 'could not unpickle: ', e
                return False
        elif split[0] == 'ARRAY':
            serial = serialized.ArraySerialized(key)
            for i in range(3):
                serial.addToPackage(self.es.readNetstring())
            try:
                obj = serial.unpack()
            except Exception, e:
                print 'could not build array: ', e
                return False
        else:
            print "Could not handle: "+''.join(split)
            return False
        
        if self.es.readNetstring() == 'GATHER OK':
            return obj
        else:
            print "Gather Failed"
            return False

    def gatherAll(self, key, style='basic'):
        """Gather from all engines.
        
        See the docstring for `gather` for more information.
        """
        return self.gather('all', key, style=style)

    def notify(self, addr=None, flag=True):
        """Instruct the controller to notify a result gatherer.
        
        :Parameters:
         - `addr`: The (ip,port) tuple of the result gatherer.
         - `flag`: A boolean to turn notification on (``True``) or off 
           (``False``)
        """
        if not self._checkConnection():
            print "Not Connected"
            return False
        
        if addr is None:
            host = socket.gethostbyname(socket.gethostname())
            port = 10104
            # print "Kernel notification: ", host, port, flag
        else:
            host, port = addr
            
        if flag:
            string = "NOTIFY ADD %s %s" % (host, port)
        else:
            string = "NOTIFY DEL %s %s" % (host, port)
        try:
            self.es.writeNetstring(string)
        except socket.error:
            try:
                self.connect()
                self.es.writeNetstring(string)
            except socket.error:
                print "Not Connected"
                return False
        
        string = self.es.readNetstring()
        if string == "NOTIFY OK":
            return True
        else:
            print "Notify Failed"
            return False

    #-------------------------------------------------------------------------------
    # Additional methods
    #-------------------------------------------------------------------------------
        
    def activate(self):
        """Make this `RemoteController` active for parallel magic commands.
        
        IPython has a magic command syntax to work with `RemoteController` objects.
        In a given IPython session there is a single active cluster.  While
        there can be many `RemoteController` created and used by the user, 
        there is only one active one.  The active `RemoteController` is used whenever 
        the magic commands %px, %pn, and %autopx are used.
        
        The activate() method is called on a given `RemoteController` to make it 
        active.  Once this has been done, the magic commands can be used.
        
        Examples
        
        >>> rc = RemoteController(('localhost',10000))
        >>> rc.activate()
        >>> %px a = 5       # Same as executeAll('a = 5')        
        >>> %pn 0 b = 10    # Same as execute(0,'b=10')
        >>> %autopx         # Now every command is sent to execute()
        ...
        >>> %autopx         # The second time it toggles autoparallel mode off
        """
        
        try:
            __IPYTHON__.activeController = self
        except NameError:
            print "The IPython Controller magics only work within IPython."
    
    def connect(self):
        """Initiate a new connection to the controller.
        
        The (ip,port) of the controller is set when the `RemoteController` 
        object is created.
        """
        
        print "Connecting to controller: ", self.addr
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error, e:
            print "Strange error creating socket: %s" % e
            return False
        try:
            self.s.connect(self.addr)
        except socket.gaierror, e:
            print "Address related error connecting to sever: %s" % e
            return False
        except socket.error, e:
            print "Not Connected: %s" % e
            return False
                
        # Turn off Nagle's algorithm to prevent the 200 ms delay :)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY,1)
        self.es = protocols.NetstringSocket(self.s)
        self.es.MAX_LENGTH = self.MAX_LENGTH
        return True
    
    def disconnect(self):
        """Disconnect from the controller.
        
        The controller and all engines are left running.
        """
        
        if self.isConnected():
            try:
                self.es.writeNetstring("DISCONNECT")
            except socket.error:
                return True
            string = self.es.readNetstring()
            if string == "DISCONNECT OK":
                self.s.close()
                del self.s
                del self.es
                return True
            else:
                print string
                return False
        else:
            return True
    
    def run(self, targets, fname):
        """Run a file on engine(s)."""
        
        fileobj = open(fname,'r')
        source = fileobj.read()
        print source
        fileobj.close()
        # if the compilation blows, we get a local error right away
        code = compile(source,fname,'exec')
        
        # Now run the code
        return self.execute(targets, source)
    
    def runAll(self, fname):
        """Run a file on all engines.
        
        See the docstring for `run` for more details.
        """
        return self.run('all', fname)
    
    def __setitem__(self, key, value):
            return self.push('all', **{key:value})
    
    def __getitem__(self, id):
        if isinstance(id, slice):
            return RemoteControllerView(self, id)
        elif isinstance(id, int):
            return EngineProxy(self, id)
        elif isinstance(id, str):
            return self.pull('all', *(id,))
        else:
            raise TypeError("__getitem__ only takes strs, ints, and slices")

    def __len__(self):
        return len(self.getIDs())
  
    def pushModule(self, mod):
        """Send a locally imported module to a kernel.
        
        This method makes a tarball of an imported module that exists 
        on the local host and sends it to the working directory of the
        kernel.  It then untars it.  
        
        After that, the module can be imported and used by the kernel.
        
        Notes:
        
        - It DOES NOT handle eggs yet.
        
        - The file must fit in the available RAM.
        
        - It will handle both single module files, as well as packages.
        
        - The byte code files (*.pyc) are not deleted.
        
        - It has not been tested with modules containing extension code,
          but it should work in most cases.
        
        - There are cross platform issues. 
        """
        
        tarball_name, fileString = tarModule(mod)
        self._pushModuleString(tarball_name, fileString)
    

    def map(self, targets, functionSource, seq, style='basic'):
        """A parallelized version of python's builtin map.
        
        This version of map is designed to work similarly to python's
        builtin map(), but the execution is done in parallel on the cluster.
                
        Example:
        
        >>> map('lambda x: x*x', range(10000))

        @arg func_code:
            A string of python code representing a cdallable.
            It must be defined in the kernels namespace.
        @arg seq:
            A python sequence to call the callable on
        """
        rtcode = self.scatter(targets, '_ipython_map_seq', seq, style='basic')
        if rtcode:
            sourceToRun = \
                '_ipython_map_seq_result = map(%s, _ipython_map_seq)' % \
                functionSource
            self.execute(targets, sourceToRun, block = False)
            return self.gather(targets, '_ipython_map_seq_result', style='basic')
        else:
            return False
            
    def mapAll(self, functionSource, seq, style='basic'):
        return self.map('all', functionSource, seq, style)

    def parallelize(self, functionName):
        return ParallelFunction(functionName, self)

#-------------------------------------------------------------------------------
# The server (Controller) side of things
#-------------------------------------------------------------------------------

class NonBlockingProducer:
    """A producer for nonblocking commands.  
    
    It waits for the consumer to perform its next write, then makes a callback.
    """

    implements(IProducer)
    
    def __init__(self, protocol):
        self.factory = protocol.factory
        self._reset()
    
    def _reset(self):
        self.consumer = None
        self.deferred = None
        self.firstCall = True
    
    def register(self, consumer, deferred):
        self.consumer = consumer
        self.deferred = deferred
        consumer.registerProducer(self, False)
    
    def resumeProducing(self):
        if self.firstCall:
            self.firstCall = False
            return
        self.deferred.callback(None)
        self.consumer.unregisterProducer()
        self._reset()
        return self.deferred
    
    def pauseProducing(self):
        pass
    
    def stopProducing(self):
        log.msg("stopped producing!")
        self._reset()
    

class VanillaControllerProtocol(protocols.EnhancedNetstringReceiver):
    """The vanilla protocol for Client/Controller communications."""
    
    nextHandler = None

    def connectionMade(self):
        log.msg("Client connection made")
        self.transport.setTcpNoDelay(True)
        self.producer = NonBlockingProducer(self)
        self._reset()
    
    def connectionLost(self, reason):
        log.msg("Client disconnected")
        
    def stringReceived(self, string):
        if self.nextHandler is None:
            self.defaultHandler(string)
        else:
            self.nextHandler(string)
    
    def dispatch(self, string):
        splitString = string.split(" ", 1)
        cmd = splitString[0]
        if len(splitString) is 1:
            args = None
            targets = 'all'
        elif len(splitString) is 2:
            arglist = splitString[1].split('::')
            args = arglist[0]
            if len(arglist) > 1:
                targets = self.parseTargets(arglist[1:])
                if not self.factory.verifyTargets(targets):
                    self._reset()
                    self.sendString("BAD ID LIST")
                    return
            else:
                targets = 'all'
        f = getattr(self, 'handle_%s' %(cmd), None)
        if f:
            # Handler resolved with state and cmd 
            f(args, targets)
        else:
            self._reset()
            self.sendString("BAD COMMAND")
    
    def handleUnexpectedData(self, args):
        self.sendString('UNEXPECTED DATA')
    
    defaultHandler = handleUnexpectedData
    
    def _reset(self):
        self.workVars = {}
        self.nextHandler = self.dispatch
    
    def parseTargets(self, targetsList):
        
        if len(targetsList) is 0:
            return 'all'
        else:
            if targetsList[0] == 'all':
                return 'all'
            try:
                return map(int, targetsList)
            except:
                #defaults to all on bad targetList  should it do this
                return None
    
    #-------------------------------------------------------------------------------
    # The GETIDS command
    #-------------------------------------------------------------------------------
    
    def handle_GETIDS(self, args, targets):
        d = self.factory.getIDs()
        return d.addCallbacks(self.getIDsCallback, self.getIDsFail)
    
    def getIDsCallback(self, idlist):
        try:
            s = pickle.dumps(idlist, 2)
        except pickle.PickleError:
            return self.getIDsFail()
        if len(s) > self.MAX_LENGTH:
            return self.getIDsFail()
        self.sendString(s)
        self.sendString("GETIDS OK")
    
    def getIDsFail(self, f):
        self.sendString("GETIDS FAIL")
    
    #-------------------------------------------------------------------------------
    # The PUSH command
    #-------------------------------------------------------------------------------
    
    def handle_PUSH(self, args, targets):
        self.nextHandler = self.handlePushing
        self.workVars['pushTargets'] = targets
        self.workVars['pushDict'] = {}
        self.sendString("PUSH READY")
    
    def handlePushing(self, args):
        if args == "PUSH DONE":
            return self.handlePushingDone()
        arglist = args.split(' ',1)
        if len(arglist) is 2:
            pushType = arglist[0]
            self.workVars['pushKey'] = arglist[1]
        else:
            self.pushFinish("FAIL")
            return
        
        f = getattr(self, 'handlePushing_%s' %pushType, None)
        if f is not None:
            self.nextHandler = f
        else:
            self.pushFinish("FAIL")
    
    def handlePushing_PICKLE(self, package):
        self.nextHandler = self.handlePushing
        key = self.workVars['pushKey']
        serial = serialized.PickleSerialized(key)
        serial.addToPackage(package)
        self.workVars['pushDict'][key] = serial
    
    def handlePushing_ARRAY(self, pShape):
        self.nextHandler = self.handlePushingArray_dtype
        key = self.workVars['pushKey']
        serial = serialized.ArraySerialized(key)
        serial.addToPackage(pShape)
        self.workVars['pushSerial'] = serial
    
    def handlePushingArray_dtype(self, dtype):
        self.nextHandler = self.handlePushingArray_buffer
        self.workVars['pushSerial'].addToPackage(dtype)
    
    def handlePushingArray_buffer(self, arrayBuffer):
        self.nextHandler = self.handlePushing
        key = self.workVars['pushKey']
        self.workVars['pushSerial'].addToPackage(arrayBuffer)
        self.workVars['pushDict'][key] = self.workVars['pushSerial']
    
    def handlePushingDone(self):
        self.nextHandler = self.handleUnexpectedData
        d = defer.Deferred().addCallback(self.pushCallback)
        self.producer.register(self.transport, d)
        self.sendString('PUSH OK')
        return d
    
    def pushCallback(self, _):
        dikt = self.workVars['pushDict']
        targets = self.workVars['pushTargets']
        self._reset()
        return self.factory.pushSerialized(targets, 
                    **dikt)
    
    def pushFinish(self,msg):
        self._reset()
        self.sendString("PUSH %s" % msg)
    
    #-------------------------------------------------------------------------------
    # The PULL command
    #-------------------------------------------------------------------------------
    
    def handle_PULL(self, args, targets):
        # Parse the args
        try:
            self.workVars['pullKeys'] = args.split(',')
        except TypeError:
            return self.pullFinish('FAIL')
        else:
            self.nextHandler = self.handleUnexpectedData
            d = self.factory.pullSerialized(targets, *self.workVars['pullKeys'])
            d.addCallbacks(self.pullOK, self.pullFail)
            return d
    
    def pullOK(self, entireResultList):
        for perTargetResultList in entireResultList:
            if len(self.workVars['pullKeys']) == 1:
                perTargetResultList = [perTargetResultList]
            for serialResult in perTargetResultList:
                if not isinstance(serialResult, serialized.Serialized):
                    try:
                        serialResult = serialized.serialize(serialResult, '_')
                    except:
                        return self.pullFail()
                self.sendSerialized(serialResult)
            
            self.sendString("SEGMENT PULLED")
        self.pullFinish("OK")
    
    def sendPickleSerialized(self, p):
            for line in p:
                self.sendString(line)
    
    def sendArraySerialized(self, a):
        for line in a[:-1]:
            self.sendString(line)
        self.sendBuffer(a[-1])
    
    def sendSerialized(self, s):
        maxlen = max(map(len, [line for line in s]))
        if maxlen > self.MAX_LENGTH:
            e = protocols.MessageSizeError(s.key)
            f = serialized.serialize(Failure(e), 'FAILURE')
            maxlen = max(map(len, [line for line in f]))
            if maxlen > self.MAX_LENGTH:
                return self.transport.loseConnection()
            return self.sendSerialized(f)
        
        if isinstance(s, serialized.PickleSerialized):
            self.sendPickleSerialized(s)
        elif isinstance(s, serialized.ArraySerialized):
            self.sendArraySerialized(s)
    
    def pullFail(self, failure):
        self.pullFinish("FAIL")
    
    def pullFinish(self, msg):
        self._reset()
        self.sendString("PULL %s" % msg)
    
    #-------------------------------------------------------------------------------
    # The PULL command
    #-------------------------------------------------------------------------------
    
    def handle_SCATTER(self, args, targets):
        if not args:
            self.nextHandler = self.handleScatter
            return
        argSplit = args.split(' ',1)
        self.workVars['scatterTargets'] = targets
        for a in argSplit:
            split = a.split('=',1)
            if len(split) is 2:
                if split[0] == 'style':
                    self.workVars['scatterStyle'] = split[1]
                elif split[0] == 'flatten':
                    self.workVars['scatterFlatten'] = int(split[1])
                else:
                    self.scatterFail()
                    return
            else:
                self.scatterFail()
                return
        self.nextHandler = self.handleScatter
    
    def handleScatter(self, args):
        arglist = args.split(' ',1)
        if len(arglist) is 2:
            scatterType = arglist[0]
            self.workVars['scatterKey'] = arglist[1]
        else:
            self.scatterFinish("FAIL")
            return
        
        f = getattr(self, 'handleScatter_%s' %scatterType, None)
        if f is not None:
            self.nextHandler = f
        else:
            self.scatterFinish("FAIL")
    
    def handleScatter_PICKLE(self, package):
        self.nextHandler = self.handleUnexpectedData
        key = self.workVars['scatterKey']
        serial = serialized.PickleSerialized(key)
        serial.addToPackage(package)
        self.workVars['scatterSerial'] = serial
        return self.handleScatterDone()
    
    def handleScatter_ARRAY(self, pShape):
        self.nextHandler = self.handleScatterArray_dtype
        key = self.workVars['scatterKey']
        serial = serialized.ArraySerialized(key)
        serial.addToPackage(pShape)
        self.workVars['scatterSerial'] = serial
    
    def handleScatterArray_dtype(self, dtype):
        self.nextHandler = self.handleScatterArray_buffer
        self.workVars['scatterSerial'].addToPackage(dtype)
    
    def handleScatterArray_buffer(self, arrayBuffer):
        self.nextHandler = self.handleUnexpectedData
        key = self.workVars['scatterKey']
        self.workVars['scatterSerial'].addToPackage(arrayBuffer)
        return self.handleScatterDone()
    
    def handleScatterDone(self):
        d = defer.Deferred().addCallback(self.scatterCallback)
        self.producer.register(self.transport, d)
        self.sendString('SCATTER OK')
        return d
    
    def scatterCallback(self, _):
        key = self.workVars['scatterKey']
        targets = self.workVars['scatterTargets']
        obj = self.workVars['scatterSerial'].unpack()
        kw = {}
        style = self.workVars.get('scatterStyle', None)
        if style is not None:
            kw['style'] = style
        flatten = self.workVars.get('scatterFlatten', None)
        if flatten is not None:
            kw['flatten'] = flatten
        self._reset()
        return self.factory.scatter(targets, key, obj, **kw)
    
    def scatterFail(self, failure=None):
        self.scatterFinish("FAIL")
    
    def scatterFinish(self, msg):
        self._reset()
        self.sendString("SCATTER "+ msg)
    
    #-------------------------------------------------------------------------------
    # The GATHER command
    #-------------------------------------------------------------------------------
    
    def handle_GATHER(self, args, targets):
        # Parse the args
        if not args:
            self.gatherFail()
        
        argSplit = args.split(' ',1)
        self.workVars['gatherKey'] = argSplit[0]
        kw = {}
        if len(argSplit) is 2:
            styleSplit = argSplit[1].split('=',1)
            if styleSplit[0] == 'style' and len(styleSplit) is 2:
                kw['style'] = styleSplit[1]
        self.nextHandler = self.handleUnexpectedData
        d = self.factory.gather(targets, self.workVars['gatherKey'], **kw)
        d.addCallbacks(self.gatherOK, self.gatherFail)
        return d
    
    def gatherOK(self, obj):
        try:
            serial = serialized.serialize(obj, self.workVars['gatherKey'])
            self.sendSerialized(serial)
        except:
            return self.gatherFail(Failure())
        self.gatherFinish("OK")
    
    def gatherFail(self, failure=None):
        self.gatherFinish("FAIL")
    
    def gatherFinish(self, msg):
        self._reset()
        self.sendString("GATHER %s" % msg)
    
    #-------------------------------------------------------------------------------
    # The EXECUTE command
    #-------------------------------------------------------------------------------
    
    def handle_EXECUTE(self, args, targets):
        """Handle the EXECUTE command."""
                
        # Parse the args
        if not args:
            self.executeFinish("FAIL")
            return
        
        if args[:5] == "BLOCK":
            block = True
            execute_cmd = args[6:]
        else:
            block = False
            execute_cmd = args
        
        if not execute_cmd:
            self.executeFinish("FAIL")
            return
        
        self.nextHandler = self.handleUnexpectedData

        if block:
            d = self.factory.execute(targets,execute_cmd)
            d.addCallback(self.executeBlockOK)
            d.addErrback(self.executeFail)
        else:
            self.workVars['execute_cmd'] = execute_cmd
            self.workVars['execute_targets'] = targets
            d = defer.Deferred().addCallback(self.executeCallback)
            self.producer.register(self.transport, d)
            self.sendString('EXECUTE OK')
            return d
    
    def executeCallback(self, _):
        execute_cmd = self.workVars['execute_cmd']
        targets = self.workVars['execute_targets']
        self._reset()
        return self.factory.execute(targets, execute_cmd)
    
    def executeBlockOK(self, results):
        for r in results:
            try:
                if isinstance(r, Failure):
                    serial = serialized.serialize(r, 'FAILURE')
                else:
                    serial = serialized.serialize(r, 'RESULT')
            except pickle.PickleError, e:
                return self.executeFinish("FAIL")
            else:
                self.sendSerialized(serial)
        self.executeFinish("OK")
    
    def executeFail(self, f):
        self.executeFinish("FAIL")
    
    def executeFinish(self, msg):
        self._reset()
        self.sendString("EXECUTE %s" % msg)
    
    #-------------------------------------------------------------------------------
    # The GETRESULT command
    #-------------------------------------------------------------------------------
    
    def handle_GETRESULT(self, args, targets):
        self.nextHandler = self.handleUnexpectedData
        try: 
            index = int(args)
        except ValueError:
            index = None
        d = self.factory.getResult(targets, index)
        d.addCallbacks(self.getResultOK, self.getResultFail)
    
    def getResultOK(self, result):
        try:
            s = serialized.serialize(result, 'RESULT')
        except pickle.pickleError:
            self.getResultFinish("FAIL")
            return
        else:
            self.sendSerialized(s)
            self.getResultFinish("OK")
    
    def getResultFail(self, f):
        self.getResultFinish("FAIL")
    
    def getResultFinish(self, msg):
        self._reset()
        self.sendString("GETRESULT %s" %msg)
    
    #-------------------------------------------------------------------------------
    # The STATUS, NOTIFY, RESET, KILL and DISCONNECT commands
    #-------------------------------------------------------------------------------
    
    def handle_STATUS(self, args, targets):
        self.nextHandler = self.handleUnexpectedData
        d = self.factory.status(targets).addCallbacks(
            self.statusOK, self.statusFail)
        return d
    
    def statusOK(self, status):
        try:
            serial = serialized.serialize(status, 'STATUS')
        except pickle.PickleError:
            return self.statusFinish('FAIL')
        else:
            self.sendSerialized(serial)
            self.statusFinish('OK')
    
    def statusFail(self, reason):
        self.statusFinish("FAIL")
    
    def statusFinish(self, msg):
        self._reset()
        self.sendString("STATUS %s" % msg)
    
    def handle_NOTIFY(self, args, targets):
        self.nextHandler = self.handleUnexpectedData
        if not args:
            self.notifyFail()
            return
        else:
            args_split = args.split(" ")
            
        if len(args_split) is 3:
            action, host, port = args_split
            try:
                port = int(port)
            except ValueError:
                return self.notifyFail()
            else:
                if action == "ADD":
                    if (host, port) in self.factory.notifiers:
                        return self.notifyOK('')
                    n = results.INotifierChild((host, port))
                    return self.factory.addNotifier(n
                    ).addCallbacks(self.notifyOK, self.notifyFail)
                elif action == "DEL":
                    return self.factory.delNotifier((host, port)
                    ).addCallbacks(self.notifyOK, self.notifyFail)
                else:
                    self.notifyFail()
        else:
            self.notifyFail()
    
    def notifyOK(self, s):
        self.notifyFinish("OK")
    
    def notifyFail(self, f=None):
        self.notifyFinish("FAIL")
    
    def notifyFinish(self, msg):
        self._reset()
        self.sendString("NOTIFY %s" % msg)
    
    def handle_RESET(self, args, targets):
        self._reset()
        self.sendString('RESET OK')
        return self.factory.reset(targets)
    
    def handle_KILL(self, args, targets):
        self._reset()
        self.sendString('KILL OK')
        return self.factory.kill(targets)
    
    def handle_DISCONNECT(self, args, targets):
        log.msg("Disconnecting client...")
        self._reset()
        self.sendString("DISCONNECT OK")
        self.transport.loseConnection()
    

class IVanillaControllerFactory(results.INotifierParent):
    """Interface to the ControllerService seen by the vanilla procotol.
    
    Not all methods of the ControllerService are needed here.  
    
     * The fooAll(...) methods are not needed as the protocol just calls 
       the foo() methods with targets='all'
     * push/pull are not needed as everything should be serialized at this point.

    But there are a number of methods implemented in 
    VanillaControllerFactoryFromService that are not implemented here.  Why?
    
    See the documentation for IMultiEngine for details about these methods.
    """
        
    def execute(self, targets, lines):
        """"""
        
    def pullNamespace(self, targets, *keys):
        """"""

    def getResult(self, targets, i=None):
        """"""
    
    def status(self, targets):
        """"""
        
    def reset(self, targets):
        """"""
        
    def kill(self, targets):
        """"""
    
    def pushSerialized(self, targets, **namespace):
        """"""
    
    def pullSerialized(self, targets, *keys):
        """"""
    
    def cleanQueue(self, targets):
        """"""
        
class VanillaControllerFactoryFromService(protocols.EnhancedServerFactory):
    """Adapt a ControllerService to a IVanillaControllerFactory implementer.
    
    This is the server factory that the controller uses to listen for client
    connections over the vanilla protocol.
    
    The methods here are those of the IMultiEngine, and documentation
    can be found in the interface definition of IMultiEngine.
    
    Where are the fooAll versions of the IMultiEngine methods?
    """
    
    implements(IVanillaControllerFactory)
    
    protocol = VanillaControllerProtocol
    
    def __init__(self, service):
        self.service = service
        self.notifiers = self.service.notifiers

    def execute(self, targets, lines):
        d = self.service.execute(targets, lines)
        return d
        
    def pullNamespace(self, targets, *keys):
        return self.service.pullNamespace(targets, *keys)
       
    def getResult(self, targets, i=None):
        return self.service.getResult(targets, i)
    
    def status(self, targets):
        return self.service.status(targets)
    
    def reset(self, targets):
        return self.service.reset(targets)
    
    def kill(self, targets):
        return self.service.kill(targets)

    def pushSerialized(self, targets, **namespace):
        return self.service.pushSerialized(targets, **namespace)
    
    def pullSerialized(self, targets, *keys):
        return self.service.pullSerialized(targets, *keys)
    
    def cleanQueue(self, targets):
        return self.service.cleanQueue(targets)
    
    def addNotifier(self, n):
        return self.service.addNotifier(n)
    
    def delNotifier(self, n):
        return self.service.delNotifier(n)
    
    def verifyTargets(self, targets):
        return self.service.verifyTargets(targets)

    def getIDs(self):
        return self.service.getIDs()

    def scatter(self, targets, key, seq, style='basic', flatten=False):
        return self.service.scatter(targets, key, seq, style, flatten)
    
    def gather(self, targets, key, style='basic'):
        return self.service.gather(targets, key, style)
    

    
components.registerAdapter(VanillaControllerFactoryFromService,
                        controllerservice.ControllerService,
                        IVanillaControllerFactory)
