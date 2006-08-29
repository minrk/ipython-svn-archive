# -*- test-case-name: ipython1.test.test_controllerclient -*-
"""The kernel interface.

The kernel interface is a set of classes that providse a high level interface
to a running ipython kernel instance.  Currently these classes use blocking
sockets and thus, do not require Twisted.

TODOs:
- Organize methods of RemoteController, RCView and EngineProxy in a consistent
  and logical manner.
- Check to make sure that RCView and EngineProxy implement all the methods they should.
- What should happen if the target given is an integer, but is not valid?
"""

#*****************************************************************************
#       Copyright (C) 2005  Fernando Perez <fperez@colorado.edu>
#                           Brian E Granger <ellisonbg@gmail.com>
#                           Benjamin Ragan-Kelly <<benjaminrk@gmail.com>>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

import socket
import pickle
import types
import os

import ipython1.kernel.magic
from twisted.python.failure import Failure
from IPython.ColorANSI import *
# from IPython.genutils import flatten as genutil_flatten


arraytypeList = []
# try:
#    import Numeric
# except ImportError:
#    pass
# else:
#    arraytypeList.append(Numeric.arraytype)
try:
    import numpy
except ImportError:
    pass
else:
    arraytypeList.append(numpy.ndarray)
# try:
#    import numarray
# except ImportError:
#    pass
# else:
#    arraytypeList.append(numarray.numarraycore.NumArray)


arraytypes = tuple(arraytypeList)
del arraytypeList

from ipython1.kernel import serialized
from ipython1.kernel.controllerservice import addAllMethods

#netstring code adapted from twisted.protocols.basic
class NetstringParseError(ValueError):
    """The incoming data is not in valid Netstring format."""
    pass

class NetstringSocket(object):
    """A wrapper for a socket that reads/writes Netstrings.
    
    This sends and receives strings over a socket, prefixing them with 
    a 4 byte integer specifying the length of the string.  This 4 byte
    integer is encoded in network byte order.
    
    Notes
    =====
        1. If extra data is received by this class it is discarded.
        2. This class might work with blocking/timeout'd sockets.
        3. No socket related exceptions are caught.
    """
    
    MAX_LENGTH = 99999999
    
    def __init__(self,sock):
        """Wrap a socket object for int32 prefixed reading/writing.
        
        The wrapped socket must be setup already.
        """
        self.sock = sock
        self._readerLength = 0
        self.__data = ''
        self.__buffer = ''
        self.verbose = False
    
    def writeNetstring(self,data):
        """Writes data to the socket.
        
        Notes
        =====
        
            1. This method uses buffers so substrings are not copied.
            2. No errors are caught currently.
        """
        if self.verbose: 
            print "client:",data
        prefix = "%d:" % len(data)
        
        offset = 0
        lengthToSend = len(prefix)
        while offset < lengthToSend:
            slice = buffer(prefix, offset, lengthToSend - offset)
            amountWritten = self.sock.send(slice)
            offset += amountWritten
            
        offset = 0
        lengthToSend = len(data)
        while offset < lengthToSend:
            slice = buffer(data, offset, lengthToSend - offset)
            if self.verbose:
                print lengthToSend, offset, len(slice), slice
            amountWritten = self.sock.send(slice)
            # print amountWritten
            offset += amountWritten
        
        return self.sock.send(',')
    
    
    def recvData(self):
        buffer,self.__data = self.__data[:self._readerLength],self.__data[self._readerLength:]
        self._readerLength = self._readerLength - len(buffer)
        self.__buffer = self.__buffer + buffer
        if self._readerLength != 0:
            return False
        else:
            return True
    
    def recvComma(self):
        if self.__data[0] != ',':
            raise NetstringParseError(repr(self.__data))
        self.__data = self.__data[1:]
        return True
    
    def recvLength(self):
        colon = self.__data.find(':')
        if colon == -1:
            return False
        try:
            self._readerLength = int(self.__data[:colon])
        except TypeError:
            return False
        else:
            self.__data = self.__data[colon+1:]
            return True
    
        
    def readNetstring(self, size=2048):
        """Reads a Netstring from the socket.
        
        Notes
        =====
            1. If there is an error, an error message is printed and
                an empty string is returned.  Change over to using exceptions.
            2. The received data is stored in a list to avoid copying strings.
            3. No socket related errors are caught currently.
        """
        # Read until we have at least 4 bytes
        while not self.recvLength():
            self.__data += self.sock.recv(size)
        while not self.recvData():
            self.__data += self.sock.recv(size)
        while not self.recvComma():
            self.__data += self.sock.recv(size)
        string = self.__buffer
        self.__buffer = ''
        if self.verbose:
            print "controller:",string
        return string
    

def _tar_module(mod):
    """Makes a tarball (as a string) of a locally imported module.
        
    This method looks at the __file__ attribute of an imported module
    and makes a tarball of the top level of the module.  It then
    reads the tarball into a binary string.  
    
    The method returns the tarball's name and the binary string
    representing the tarball.
    
    Notes:
    
    - It will handle both single module files, as well as packages.
    
    - The byte code files (*.pyc) are not deleted.
    
    - It has not been tested with modules containing extension code,
      but it should work in most cases.
      
    - There are cross platform issues. 
    """
     
    if not isinstance(mod, types.ModuleType):
        raise TypeError, "Pass an imported module to push_module"
    module_dir, module_file = os.path.split(mod.__file__)
    
    # Figure out what the module is called and where it is
    print "Locating the module..."
    if "__init__.py" in module_file:  # package
        module_name = module_dir.split("/")[-1]
        module_dir = "/".join(module_dir.split("/")[:-1])
        module_file = module_name
    else:                             # Simple module
        module_name = module_file.split(".")[0]
        module_dir = module_dir
    print "Module (%s) found in:\n%s" % (module_name, module_dir)
        
    # Make a tarball of the module in the cwd
    if module_dir:
        os.system('tar -cf %s.tar -C %s %s' % \
            (module_name, module_dir, module_file))
    else:   # must be the cwd
        os.system('tar -cf %s.tar %s' % \
            (module_name, module_file))
    
    # Read the tarball into a binary string        
    tarball_name = module_name + ".tar"
    tar_file = open(tarball_name,'rb')
    fileString = tar_file.read()
    tar_file.close()
    
    # Remove the local copy of the tarball
    #os.system("rm %s" % tarball_name)
    
    return tarball_name, fileString


class EngineProxy(object):
    """an object to interact directly to a remote engine through a Remote 
    Controller object.  Primarily generated by the dictionary interface of 
    RemoteController or RCView"""
    
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
    
    def __setitem__(self, key, value):
        return self.push(**{key:value})
    
    def pull(self, *keys):
        return self.rc.pull(self.id, *keys)
    
    def __getitem__(self, key):
        return self.pull(*(key,))
    
    def pullNamespace(self, *keys):
        return self.rc.pullNamespace(self.id, *keys)
    
    def status(self):
        return self.rc.status(self.id)
    
    def getResult(self, i=None):
        return self.rc.getResult(self.id, i)
    
    def reset(self):
        return self.rc.reset(self.id)
    
    def kill(self):
        return self.rc.kill(self.id)
    


class RCView(object):
    """A subset interface for RemoteController.__getitem__"""
    def __init__(self, rc, ids):
        self.rc = rc
        if isinstance(ids, slice):
            self._originalIDs = range(*ids.indices(ids.stop))
        elif isinstance(ids, list):
            self._originalIDs = ids
        else:
            raise TypeError("RCView requires slice or list")
        # Make sure these exist as of now
        currentIDs = rc.getIDs()
        for id in self._originalIDs:
            if id not in currentIDs:
                raise Exception("The engine with id %i does not exist" % id)
        self._ids = range(len(self._originalIDs))
        print self._ids
        print self._originalIDs
        addAllMethods(self)
    
    def getIDs(self):
        return self._originalIDs
        
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
    
    def execute(self, targets, lines, block=False):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.execute(actualTargets, lines, block)
    
    def push(self, targets, **namespace):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.push(actualTargets, **namespace)
    
    def __setitem__(self, key, value):
        return self.push(**{key:value})
    
    def pull(self, targets, *keys):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.pull(actualTargets, *keys)
    
    def __getitem__(self, id):
        if isinstance(id, slice):
            return RCView(self.rc, self._originalIDs[id])
        elif isinstance(id, int):
            return EngineProxy(self.rc, self._originalIDs[id])
        elif isinstance(id, str):
            return self.pull('all',*(id,))
        else:
            raise TypeError("__getitem__ only takes strs, ints, and slices")
    
    def run(self, targets, fname):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.run(actualTargets, fname)
    
    def pullNamespace(self, targets, *keys):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.pullNamespace(actualTargets, *keys)
    
    def status(self, targets):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.status(actualTargets)
    
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.scatter(actualTargets, key, seq, style, flatten)
    
    def gather(self, targets, key, style='basic'):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.gather(actualTargets, key, style)        
    
    def getResult(self, targets, i=None):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.getResult(actualTargets, i)
    
    def reset(self, targets):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.reset(actualTargets)
    
    def kill(self, targets):
        actualTargets = self._mapIDsToOriginal(targets)
        return self.rc.kill(actualTargets)
    
    def activate(self):
        try:
            __IPYTHON__.active_cluster = self
        except NameError:
            print "The %px and %autopx magic's are not active."
    


class RemoteController(object):
    """A high level interface to a remotely running ipython controller."""
    
    def __init__(self, addr):
        """Create a RemoteController instance pointed at a specific controller.
        
        @arg addr:
            The (ip,port) tuple of the kernel.  The ip in a string
            and the port is an int.
        """
        self.addr = addr
        self.block = False
        addAllMethods(self)
    
    def activate(self):
        """Make this cluster the active one for ipython magics.
        
        IPython has a magic syntax to work with InteractiveCluster objects.
        In a given ipython session there is a single active cluster.  While
        there can be many clusters created and used by the user, there is only
        one active one.  The active cluster is used when ever the magic syntax
        is used.  
        
        The activate() method is called on a given cluster to make it the active
        one.  Once this has been done, the magic command can be used:
        
        >>> %px a = 5       # Same as execute('a = 5')
        
        >>> %autopx         # Now every command is sent to execute()
        
        >>> %autopx         # The second time it toggles autoparallel mode off
        """
        try:
            __IPYTHON__.active_cluster = self
        except NameError:
            print "The %px and %autopx magic's are not active."
    
    def __del__(self):
        return self.disconnect()
    
    def is_connected(self):
        """Are we connected to the controller?""" 
        if hasattr(self, 'es'):
            try:
                self.es.writeNetstring('')
                self.es.readNetstring()
            except socket.error:
                return False
            else:
                return True
    
    def _check_connection(self):
        """Are we connected to the controller?  If not reconnect."""
        if not self.is_connected():
            self.connect()
    
    def connect(self):
        """Initiate a new connection to the controller."""
        
        print "Connecting to controller: ", self.addr
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error, e:
            print "Strange error creating socket: %s" % e
            
        try:
            self.s.connect(self.addr)
        except socket.gaierror, e:
            print "Address related error connecting to sever: %s" % e
        except socket.error, e:
            print "Connection error: %s" % e
                
        # Turn off Nagle's algorithm to prevent the 200 ms delay :)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY,1)
        self.es = NetstringSocket(self.s)
    
    def parseTargets(self, targets):
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
    
    def multiTargets(self, targets):
        return not isinstance(targets, int) and len(targets) > 1
    
    def executeAll(self, source, block=False):
        return self.execute('all', source, block)
    
    def execute(self, targets, source, block=False):
        """Execute python source code on the ipython kernel.
        
        @arg targets:
            the engine id(s) on which to execute.  targets can be an int, list of
            ints, or the string 'all' to indicate that it should be executed on
            all engines connected to the controller.
        @arg source:
            A string containing valid python code
        @arg block:
            whether or not to wait for the results of the command.
            True:
                wait for results, which will be printed as stdin/out/err
            False:
                do not wait, return as soon as source has been sent, print nothing.
        """
        targetstr = self.parseTargets(targets)
        if not targetstr or not source:
            # need something to do
            return False
        self._check_connection()
        
        if self.block or block:
            self.es.writeNetstring("EXECUTE BLOCK %s::%s" % (source, targetstr))
            string = self.es.readNetstring()
            if string [:3] == 'BAD':
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
            self.es.writeNetstring(string)
            string = self.es.readNetstring()
            data = None
             
        if string == "EXECUTE OK":
            return True
        else:
            return False
    
    def run(self, targets, fname):
        """Run a file on the kernel."""
        
        fileobj = open(fname,'r')
        source = fileobj.read()
        fileobj.close()
        # if the compilation blows, we get a local error right away
        code = compile(source,fname,'exec')
        
        # Now run the code
        return self.execute(targets, source)
    
    def runAll(self, fname):
        return self.run('all', fname)
    
    def sendSerial(self, serial):
        assert isinstance(serial, serialized.Serialized)
        for line in serial:
            self.es.writeNetstring(line)
    
    def push(self, targets, **namespace):
        """Send python object(s) to the namespace of remote kernel(s).
        
        There is also a dictionary style interface to the push command:
                
        >>> rc = RemoteController(addr)
        
        >>> rc[0]['a'] = 10    # Same as rc.push(0, a=10)
        >>> rc.push([1,2,3], a=5, b=[1], c=c)
            #pushes 5 to a, [1] to b, and the local value c to c on engines [1,2,3]
        
        @arg targets:
            the engine id(s) on which to execute.  targets can be an int, list of
            ints, or the string 'all' to indicate that it should be executed on
            all engines connected to the controller.
        @arg namespace:
            The python objects to send and their remote keys.  i.e. a=1, b='asdf'
        """
        targetstr = self.parseTargets(targets)
        if not targetstr or not namespace:
            #need something to do
            return False
        self._check_connection()        
        
        self.es.writeNetstring("PUSH ::%s" % targetstr)
        if self.es.readNetstring() != "PUSH READY":
            return False
        for key in namespace:
            value = namespace[key]
            try:
                serialObject = serialized.serialize(value, key)
            except Exception, e:
                print "Object cannot be serialized: ", key, e
                return False
            else:
                self.sendSerial(serialObject)
        self.es.writeNetstring("PUSH DONE")
        string = self.es.readNetstring()
        if string == "PUSH OK":
            return True
        elif string == "PUSH FAIL":
            return False
        else:
            return string
    
    def __setitem__(self, key, value):
            return self.push('all', **{key:value})
    
    def pull(self, targets, *keys):
        """Get python object(s) from remote kernel(s).
                
        If the object does not exist in the kernel's namespace a NotDefined
        object will be returned.
        
        Like push, pull also has a dictionary interface:
        
        >>> rc = RemoteController(addr)
        >>> rc[0]['a'] = 10    # Same as rc.push(0, a=10)
        >>> rc[0]['a']         # Same as rc.pull(0,'a')
        10
        
        @arg targets:
            the engine id(s) on which to execute.  targets can be an int, list of
            ints, or the string 'all' to indicate that it should be executed on
            all engines connected to the controller.
        @arg *keys:
            The name of the python objects to get
        
        @returns:
            4 cases:
                1 target, 1 key:
                    the value of key on target
                1 target, >1 keys:
                    a list of the values of keys on target
                >1 targets, 1 key:
                    a tuple of the values at key on targets
                >1 targets, >1 keys:
                    a list of length len(keys) of tuples for each key on targets.
                    equivalent in form to:
                    l = []
                    for t in targets:
                        l.append(rc.pull(t, *keys))
        """
        targetstr = self.parseTargets(targets)
        if not targetstr or not keys:
            # need something to do
            return False
        self._check_connection()
        
        try:
            keystr = ','.join(keys)
        except TypeError:
            return False
        
        multitargets = self.multiTargets(targets)
        self.es.writeNetstring("PULL %s::%s" % (keystr, targetstr))
        string = self.es.readNetstring()
        if string [:3] == 'BAD':
            return False
        results = []
        returns = []
        while string not in ['PULL OK', 'PULL FAIL']:
            string_split = string.split(' ', 1)
            if len(string_split) is not 2:
                return False
            if string_split[0] == "PICKLE":
                #if it's a pickle
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
                    return False    
                for i in range(3):#arrays have a 3 line package
                    sArray.addToPackage(self.es.readNetstring())
                data = sArray.unpack()
            else:
                #we don't know how to handle it!
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
            return False
    
    def __getitem__(self, id):
        if isinstance(id, slice):
            return RCView(self, id)
        elif isinstance(id, int):
            return EngineProxy(self, id)
        elif isinstance(id, str):
            return self.pull('all', *(id,))
        else:
            raise TypeError("__getitem__ only takes strs, ints, and slices")
    
    def pullNamespace(self, targets, *keys):
        """Gets a namespace dict with keys from targets.  This is just a wrapper
        for pull, to construct namespace dicts from the results of pull.
        
        returns:
            1 target:
                a dictionary of keys/values on remote engine
            >1 targets:
                a list of dictionaries of the form of 1 target.  Order of targets
                is maintained.
                
            """
        targetstr = self.parseTargets(targets)
        if not targetstr or not keys:
            # need something to do
            return False
        self._check_connection()
        
        multitargets = self.multiTargets(targets)
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
    
    def scatter(self, targets, key, seq, style='basic', flatten=False):
        """distribute sequence object to targets"""
        targetstr = self.parseTargets(targets)
        if not targetstr or not key or \
            not isinstance(seq, (tuple, list)+arraytypes):
            return False
        self._check_connection()
        
        try:
            serial = serialized.serialize(seq, key)
        except:
            return False
        self.es.writeNetstring('SCATTER style=%s flatten=%i::%s' %
                (style, int(flatten), targetstr))
        self.sendSerial(serial)
        reply = self.es.readNetstring()
        if reply == 'SCATTER OK':
            return True
        else:
            return False
    
    def gather(self, targets, key, style='basic'):
        """gather a distributed object, and reassemble it"""
        targetstr = self.parseTargets(targets)
        if not targetstr or not key:
            return False
        self._check_connection()
        
        self.es.writeNetstring('GATHER %s style=%s::%s' %(key, style, targetstr))
        split = self.es.readNetstring().split(' ',1)
        if len(split) is not 2:
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
            return False
        
        if self.es.readNetstring() == 'GATHER OK':
            return obj
        else:
            return False
    
    def getResult(self, targets, i=None):
        """Gets a specific result from the kernels, returned as a tuple, or 
            list of tuples if multiple targets."""
        targetstr = self.parseTargets(targets)
        if not targetstr:
            # need something to do
            return False
        self._check_connection()    
        
        if i is None:
            self.es.writeNetstring("GETRESULT ::%s" %targetstr)
        else:
            self.es.writeNetstring("GETRESULT %i::%s" % (i, targetstr))
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
                    if not self.multiTargets(targets):
                        data = data[0]
                    return data
                else:
                    print string
                    return False
        else:
            # For other data types
            print string
            return False
    
    def status(self, targets):
        """Check the status of the kernel."""
        targetstr = self.parseTargets(targets)
        if not targetstr:
            # need something to do
            return False
        self._check_connection()
        
        self.es.writeNetstring("STATUS ::%s" %targetstr)
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
                    if not self.multiTargets(targets):
                        data = data[0][1]
                    return data
                else:
                    return False
        else:
            return False
    
    def getIDs(self):
        status = self.statusAll()
        if(status):
            return zip(*self.statusAll())[0]
        else:
            return status
    
    def notify(self, addr=None, flag=True):
        """Instruct the kernel to notify a result gatherer.
        
        When the IPython kernel runs code, it traps the stdout and stderr
        of each command and stores them in a list.  The tuple of stdin, stdout
        and stderr of each executed command is called the result of the command.
        
        The result of each command is sent by the kernel to the user who 
        collects and handles the results using instances of the ResultGatherer
        class.  This class is bound to a UDP port and handles results from one
        or more kernels that are sending results to the ResultGatherer.
        
        This design was choosen to allow complete flexibility in monitoring
        the activity of groups of ipython kernels.  Each kernel keeps a list of    
        (ip, port) tuples to which results should be sent.  New addresses are
        added to this list using the notify() method.  This way each kernel can
        send results to multple observers and each observer can watch a 
        different set of kernels. 
            
        @arg addr:
            The (ip, port) tuple of the result gatherer
        @arg flag:
            A boolean to turn notification on (True) or off (False) 
        """
        self._check_connection()
        
        if addr is None:
            host = socket.gethostbyname(socket.gethostname())
            port = 10104
            # print "Kernel notification: ", host, port, flag
        else:
            host, port = addr
            
        if flag:
            self.es.writeNetstring("NOTIFY ADD %s %s" % (host, port))
        else:
            self.es.writeNetstring("NOTIFY DEL %s %s" % (host, port))
        string = self.es.readNetstring()
        if string == "NOTIFY OK":
            return True
        else:
            return False
    
    def reset(self, targets):
        """Clear the namespace if the kernel."""
        targetstr = self.parseTargets(targets)
        if not targetstr:
            # need something to do
            return False
        self._check_connection()
        
        self.es.writeNetstring("RESET ::%s" %targetstr)
        string = self.es.readNetstring()
        if string == "RESET OK":
            return True
        else:
            return False      
    
    def kill(self, targets):
        """Kill the engine completely."""
        targetstr = self.parseTargets(targets)
        if not targetstr:
            # need something to do
            return False
        self._check_connection()    
        
        self.es.writeNetstring("KILL ::%s" %targetstr)
        string = self.es.readNetstring()
        if string == "KILL OK":
            return True
        else:
            return False      
    
    def disconnect(self):
        """Disconnect from the kernel, but leave it running."""
        if self.is_connected():
            self.es.writeNetstring("DISCONNECT")
            string = self.es.readNetstring()
            if string == "DISCONNECT OK":
                self.s.close()
                del self.s
                del self.es
                return True
            else:
                return False
        else:
            return True
    
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
        
        tarball_name, fileString = _tar_module(mod)
        self._push_moduleString(tarball_name, fileString)
    
    def _push_moduleString(self, tarball_name, fileString):
        """This method send a tarball'd module to a kernel."""
        
        self.push('tar_fileString',fileString)
        self.execute("tar_file = open('%s','wb')" % \
            tarball_name, block=False)
        self.execute("tar_file.write(tar_fileString)", block=False)
        self.execute("tar_file.close()", block=False)
        self.execute("import os", block=False)
        self.execute("os.system('tar -xf %s')" % tarball_name)        
    

    
