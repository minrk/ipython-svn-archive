# -*- test-case-name: ipython1.test.test_controllerclient -*-
"""The kernel interface.

The kernel interface is a set of classes that providse a high level interface
to a running ipython kernel instance.  Currently these classes use blocking
sockets and thus, do not require Twisted.  
"""
#*****************************************************************************
#       Copyright (C) 2005  Brian Granger, <bgranger@scu.edu>
#                           Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************
import socket
import threading
import pickle
import types
import time, os

from twisted.internet import defer

from IPython.ColorANSI import *
from IPython.genutils import flatten as genutil_flatten

try: 
    import numpy
except ImmportError:
    numpy = None

try:
    from ipython1.kernel import serialized
except ImportError:
    print "ipython1 needs to be in your PYTHONPATH"

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
    
    def writeString(self,data):
        """Writes data to the socket.
        
        Notes
        =====
        
            1. This method uses buffers so substrings are not copied.
            2. No errors are caught currently.
        """
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
            amountWritten = self.sock.send(slice)
            offset += amountWritten
        
        self.sock.send(',')
    
    
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
    
        
    def readString(self, size=2048):
        """Reads an int32 prefixed string from the socket.
        
        THIS IS BROKEN RIGHT NOW!!
        
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
    Controller object"""
    
    def __init__(self, rc, id):
        self.id = id
        self.rc = rc
    
    def execute(self, strings, block=False):
        if block:
            return self.rc.execute(self.id, strings, block=True)[0]
        else:
            return self.rc.execute(self.id, strings)
    
    def push(self, key, value):
        return self.rc.push(self.id, key, value)
    
    def __setitem__(self, key, value):
        return self.push(key,value)
    
    def pull(self, *keys):
        return self.rc.pull(self.id, *keys)
    
    def __getitem__(self, key):
        return self.pull(*(key))
    
    def status(self):
        return self.rc.status(self.id)
    
    def getResult(self, n=None):
        return self.rc.getResult(self.id, n)
    
    def reset(self):
        return self.rc.reset(self.id)
    
    def kill(self):
        return self.rc.kill(self.id)
    


class SubCluster(object):
    """A set of EngineProxy objects for RemoteController.__getitem__"""
    def __init__(self, rc, ids):
        self.rc = rc
        if isinstance(ids, slice):
            #parse slice
            idlist = rc.status().keys()
            if ids.step is None:
                step = 1
            else:
                step = ids.step
            if ids.start is None:
                start = min(idlist)
            else:
                start = ids.start
            if ids.stop is None:
                stop = max(idlist)
            else:
                stop = ids.stop
            self.ids = range(start, stop, step)
        elif isinstance(ids, list):
            self.ids = ids
        else:
            raise TypeError("SubCluster requires slice or list")
    
    def execute(self, strings, block=False):
            return self.rc.execute(self.ids, strings, block)
    
    def push(self, key, value):
        return self.rc.push(self.ids, key, value)
    
    def __setitem__(self, key, value):
        return self.push(key,value)
    
    def pull(self, *keys):
        return self.rc.pull(self.ids, *keys)
    
    def __getitem__(self, id):
        if isinstance(id, slice):
            return SubCluster(self.rc, self.ids[id])
        elif isinstance(id, int):
            return EngineProxy(self.rc, self.ids[id])
        elif isinstance(id, str):
            return self.pull(*(id))
        else:
            raise TypeError("__getitem__ only takes strs, ints, and slices")
    
    def status(self):
        return self.rc.status(self.ids)
    
    def getResult(self, n=None):
        return self.rc.getResult(self.ids, n)
    
    def reset(self):
        return self.rc.reset(self.ids)
    
    def kill(self):
        return self.rc.kill(self.ids)
    


class RemoteController(object):
    """A high level interface to a remotely running ipython kernel."""
    
    def __init__(self, addr):
        """Create a RemoteController instance pointed at a specific kernel.
        
        Upon creation, the RemoteController class knows about, but is not
        connected to the kernel.  The connection occurs automatically when
        other methods of RemoteController are called.
        
        @arg addr:
            The (ip,port) tuple of the kernel.  The ip in a string
            and the port is an int.
        """
        self.addr = addr
        self.block = False
    
    def __del__(self):
        return self.disconnect()
    
    def is_connected(self):
        """Are we connected to the kernel?""" 
        if hasattr(self, 's'):
            try:
                self.fd = self.s.fileno()
            except socket.error:
                return False
            else:
                return True
    
    def _check_connection(self):
        """Are we connected to the kernel, if not reconnect."""
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
    
    def execute(self, targets, source, block=False):
        """Execute python source code on the ipython kernel.
        
        @arg source:
            A string containing valtargets python code
        """
        self._check_connection()
        if isinstance(targets, list):
            targets = '::'.join(map(str, targets))
        if self.block or block:
            self.es.writeString("EXECUTE BLOCK %s::%s" % (source, targets))
            string = self.es.readString()
            if string == "PICKLE RESULT":
                package = self.es.readString()
                try:
                    data = pickle.loads(package)
                    string = self.es.readString()
                except pickle.PickleError, e:
                    print "Error unpickling object: ", e
                    return False    
                
                # Now print data
                blue = TermColors.Blue
                normal = TermColors.Normal
                red = TermColors.Red
                green = TermColors.Green
                for d in data:
#                    (targets, cmd) = d
                    cmd = d
                    targets = 0
                    cmd_num = cmd[0]
                    cmd_stdin = cmd[1]
                    cmd_stdout = cmd[2][:-1]
                    cmd_stderr = cmd[3][:-1]
                    print "%s[%s]:[%i]%s In [%i]:%s %s" % \
                        (green, self.addr[0], targets,
                        blue, cmd_num, normal, cmd_stdin)
                    if cmd_stdout:
                        print "%s[%s]:[%i]%s Out[%i]:%s %s" % \
                            (green, self.addr[0], targets,
                            red, cmd_num, normal, cmd_stdout)
                    if cmd_stderr:
                        print "%s[%s]:[%i]%s Err[%i]:\n%s %s" % \
                            (green, self.addr[0], targets,
                            red, cmd_num, normal, cmd_stderr)
            else:
                data = None
                string = ""
        else:
            string = "EXECUTE %s::%s" % (source, targets)
            self.es.writeString(string)
            string = self.es.readString()
            data = None
             
        if string == "EXECUTE OK":
            return True
        else:
            return False
    
    def run(self, fname):
        """Run a file on the kernel."""
        
        fileobj = open(fname,'r')
        source = fileobj.read()
        fileobj.close()
        # if the compilation blows, we get a local error right away
        code = compile(source,fname,'exec')
        
        # Now run the code
        self.execute(source)
    
    def push(self, targets, **namespace):
        """Send a python object to the namespace of a kernel.
        
        There is also a dictionary style interface to the push command:
                
        >>> rc = RemoteController(addr)
        
        >>> rc['a'] = 10    # Same as rc.push('a', 10)
        
        @arg value:
            The python object to send
        @arg key:
            What to name the object in the kernel' namespace
        """
        self._check_connection()
        if isinstance(targets, list):
            targets = '::'.join(map(str, targets))
        serializedNamespace = []
        for key in namespace:
            value = namespace[key]
            if False:#this does not work yet; isinstance(value, numpy.array):
                try:
                    serialObject = serialized.ArraySerialized(key)
                    serialObject.packObject(value)
                except Exception, e:
                    print "Object cannot be serialized: ", e
                    return False
            else:    
                try:
                    serialObject = serialized.PickleSerialized(key)
                    serialObject.packObject(value)
                except pickle.PickleError, e:
                    print "Object cannot be pickled: ", e
                    return False
            serializedNamespace.append(serialObject)
        self.es.writeString("PUSH ::%s" % targets)
        if self.es.readString() != "PUSH READY":
            return False
        for sObj in serializedNamespace:
            for line in sObj:
                self.es.writeString(line)
        self.es.writeString("PUSH DONE")
        string = self.es.readString()
        if string == "PUSH OK":
            return True
        elif string == "PUSH FAIL":
            return False
        else:
            return string
    
    def __setitem__(self, key, value):
            return self.push('all', key, value)
    
    def pull(self, targets, *keys):
        """Get a python object from a remote kernel.
                
        If the object does not exist in the kernel's namespace a NotDefined
        object will be returned.
        
        Like push, pull also has a dictionary interface:
        
        >>> rc = RemoteController(addr)
        >>> rc['a'] = 10    # Same as rc.push('a', 10)
        >>> rc['a']         # Same as rc.pull('a')
        10
        
        @arg key:
            The name of the python object to get        
        """
        self._check_connection()    
        if isinstance(targets, list):
            targets = '::'.join(map(str, targets))
        try:
            keystr = ','.join(keys)
        except TypeError:
            return False
        
        self.es.writeString("PULL %s::%s" % (keystr, targets))
        string = self.es.readString()
        results = []
        returns = []
        nkeys = len(keys)
        while string not in ['PULL OK', 'PULL FAIL']:
            print string
            string_split = string.split(' ', 1)
            if len(string_split) is not 2:
                return False
            if string_split[0] == "PICKLE":
                #if it's a pickle
                sPickle = serialized.PickleSerialized(string_split[1])
                sPickle.addToPackage(self.es.readString())
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
                    sArray.addToPackage(self.es.readString())
                data = sArray.unpack()
            else:
                #we don't know how to handle it!
                return False
            
            #successful retrieval
            results.append(data)
            #get next string and reenter loop
            string = self.es.readString()
            if string == "SEGMENT PULLED":
                returns.append(results)
                results = []
                string = self.es.readString()
        #finish command
        if not returns:
            #if it was not a nested list
            returns = results   
        if string == 'PULL OK':
            if len(returns) is 1:
                returns = returns[0]
            return returns
        else:
            return False
        
    def __getitem__(self, id):
        if isinstance(id, slice):
            return SubCluster(self, id)
        elif isinstance(id, int):
            return EngineProxy(self, id)
        elif isinstance(id, str):
            return self.pull('all', *(id))
        else:
            raise TypeError("__getitem__ only takes strs, ints, and slices")
    
    def getResult(self, targets, number=None):
        """Gets a specific result from the kernel, returned as a tuple."""
        self._check_connection()    
        if isinstance(targets, list):
            targets = '::'.join(map(str, targets))
        
        if number is None:
            self.es.writeString("GETRESULT ::%s" %targets)
        else:
            self.es.writeString("GETRESULT %i::%s" % (number, targets))
        string = self.es.readString()
        if string == "PICKLE RESULT":
            package = self.es.readString()
            string = self.es.readString()
            try:
                data = pickle.loads(package)
            except pickle.PickleError, e:
                print "Error unpickling object: ", e
                return False
            else:
                if string == "GETRESULT OK":
                    return data
                else:
                    return False
        else:
            # For other data types
            return False
    
    def status(self, targets):
        """Check the status of the kernel."""
        self._check_connection()
        if isinstance(targets, list):
            targets = '::'.join(map(str, targets))
        
        self.es.writeString("STATUS ::%s" %targets)
        string = self.es.readString()
        if string == "PICKLE STATUS":
            package = self.es.readString()
            string = self.es.readString()
            try:
                data = pickle.loads(package)
            except pickle.PickleError, e:
                print "Error unpickling object: ", e
                return False
            else:
                if string == "STATUS OK":
                    return data
                else:
                    return False
        else:
            # For other data types
            pass
    
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
#            print "Kernel notification: ", host, port, flag
        else:
            host, port = addr
            
        if flag:
            self.es.writeString("NOTIFY ADD %s %s" % (host, port))
        else:
            self.es.writeString("NOTIFY DEL %s %s" % (host, port))
        string = self.es.readString()
        if string == "NOTIFY OK":
            return True
        else:
            return False
    
    def reset(self, targets):
        """Clear the namespace if the kernel."""
        self._check_connection()
        if isinstance(targets, list):
            targets = '::'.join(map(str, targets))
        
        self.es.writeString("RESET ::%s" %targets)
        string = self.es.readString()
        if string == "RESET OK":
            return True
        else:
            return False      
    
    def kill(self, targets):
        """Kill the engine completely."""
        self._check_connection()    
        if isinstance(targets, list):
            targets = '::'.join(map(str, targets))
        
        self.es.writeString("KILL ::%s" %targets)
        string = self.es.readString()
        if string == "KILL OK":
            return True
        else:
            return False      
    
    def disconnect(self):
        """Disconnect from the kernel, but leave it running."""
        if self.is_connected():
            self.es.writeString("DISCONNECT")
            string = self.es.readString()
            if string == "DISCONNECT OK":
                self.s.close()
                del self.s
                del self.es
                return True
            else:
                return False
        else:
            return True
    
    def push_module(self, mod):
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
    

    
