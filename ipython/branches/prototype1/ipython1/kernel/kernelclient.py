"""The kernel interface.

The kernel interface is a set of classes that provide a high level interface
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

from IPython.ColorANSI import *
from IPython.genutils import flatten as genutil_flatten
from IPython.genutils import get_home_dir, file_readlines, filefind

import ipython1.kernel.map as map
from ipython1.kernel.parallelfunction import ParallelFunction

from ipython1.kernel.esocket import LineSocket
import ipython1.kernel.kernel_magic
from ipython1.kernel.kernelerror import NotDefined
           
# Utility functions
           
def _tarModule(mod):
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
    file_string = tar_file.read()
    tar_file.close()
    
    # Remove the local copy of the tarball
    #os.system("rm %s" % tarball_name)
    
    return tarball_name, file_string
               
# The main classes
                    
class RemoteKernel(object):
    """A high level interface to a remotely running ipython kernel."""
    
    def __init__(self, addr):
        """Create a RemoteKernel instance pointed at a specific kernel.
        
        Upon creation, the RemoteKernel class knows about, but is not
        connected to the kernel.  The connection occurs automatically when
        other methods of RemoteKernel are called.
        
        @arg addr:
            The (ip,port) tuple of the kernel.  The ip in a string
            and the port is an int.
        """
        self.addr = addr
        self.extra = ''
        self.block = False
        
    def __del__(self):
        self.disconnect()
        
    def isConnected(self):
        """Are we connected to the kernel?""" 
        if hasattr(self, 's'):
            try:
                self.fd = self.s.fileno()
            except socket.error:
                return False
            else:
                return True
                
    def _checkConnection(self):
        """Are we connected to the kernel, if not reconnect."""
        if not self.isConnected():
            self.connect()
            
    def connect(self):
        """Initiate a new connection to the kernel."""
        
        print "Connecting to kernel: ", self.addr
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
                
        self.es = LineSocket(self.s)
        # Turn of Nagle's algorithm to prevent the 200 ms delay :)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY,1)

    # Methods in the Interface
        
    def execute(self, lines, block=False):
        """Execute python source code on the ipython kernel.
        
        @arg source:
            A string containing valid python code
        """
        self._checkConnection()
        if self.block or block:
            self.es.write_line("EXECUTE BLOCK %s" % lines)
            line, self.extra = self.es.read_line(self.extra)
            line_split = line.split(" ")
            if line_split[0] == "PICKLE" and len(line_split) == 2:
                try:
                    nbytes = int(line_split[1])
                except:
                    print "Server did not return the length of data."
                    return False
                package, self.extra = self.es.read_bytes(nbytes, self.extra)
                data = pickle.loads(package)
                line, self.extra = self.es.read_line(self.extra)
                
                # Now print data
                blue = TermColors.Blue
                normal = TermColors.Normal
                red = TermColors.Red
                green = TermColors.Green
                cmd_num = data[0]
                cmd_stdin = data[1]
                cmd_stdout = data[2][:-1]
                cmd_stderr = data[3][:-1]
                print "%s[%s]%s In [%i]:%s %s" % \
                    (green, self.addr[0],
                    blue, cmd_num, normal, cmd_stdin)
                if cmd_stdout:
                    print "%s[%s]%s Out[%i]:%s %s" % \
                        (green, self.addr[0],
                        red, cmd_num, normal, cmd_stdout)
                if cmd_stderr:
                    print "%s[%s]%s Err[%i]:\n%s %s" % \
                        (green, self.addr[0],
                        red, cmd_num, normal, cmd_stderr)
            else:
                data = None
                line = ""
        else:
            self.es.write_line("EXECUTE %s" % lines)
            line, self.extra = self.es.read_line(self.extra)
            data = None
             
        if line == "EXECUTE OK":
            return None
        else:
            return False

    def run(self, filename):
        """Run a file on the kernel."""

        fileobj = open(fname,'r')
        source = fileobj.read()
        fileobj.close()
        # if the compilation blows, we get a local error right away
        code = compile(source,fname,'exec')
        
        # Now run the code
        self.execute(source)
        
    def _push(self, key, value):
        """Send a python object to the namespace of a kernel.
        
        There is also a dictionary style interface to the push command:
                
        >>> rk = RemoteKernel(addr)
        
        >>> rk['a'] = 10    # Same as rk.push('a', 10)
        
        @arg value:
            The python object to send
        @arg key:
            What to name the object in the kernel' namespace
        @arg forward:
            Boolean that determines if the object should be forwarded
            Not implemented.
        """
        self._checkConnection()
        try:
            package = pickle.dumps(value, 2)
        except pickle.PickleError, e:
            print "Object cannot be pickled: ", e
            return False
        self.es.write_line("PUSH %s" % key )
        self.es.write_line("PICKLE %i" % len(package))
        self.es.write_bytes(package)
        line, self.extra = self.es.read_line(self.extra)
        if line == "PUSH OK":
            return True
        if line == "PUSH FAIL":
            return False
        
    def push(self, **namespace):
        """Send the dict of key value pairs to the kernel's namespace.
        
        >>> rk = RemoteKernel(addr)
        >>> rk.update({'a':1,'b':2,'c':'mystring})    
        # sends a, b and c to the kernel
        
        @arg dict:
            A dictionary of key, value pairs to send to the kernel
        """
        for key, value in namespace.iteritems():
            self._push(key, value)
        
    def pull(self, *keys):
        result = []
        for k in keys:
            result.append(self._pull(k))
        if len(keys) == 1:
            return result[0]
        else:
            return tuple(result)
        
    def _pull(self, key):
        """Get a python object from a remote kernel.
                
        If the object does not exist in the kernel's namespace a NotDefined
        object will be returned.
        
        Like push, pull also has a dictionary interface:

        >>> rk = RemoteKernel(addr)
        >>> rk['a'] = 10    # Same as rk.push('a', 10)
        >>> rk['a']         # Same as rk.pull('a')
        10
        
        @arg key:
            The name of the python object to get        
        """
        self._checkConnection()    
    
        self.es.write_line("PULL %s" % key)
        line, self.extra = self.es.read_line(self.extra)
        line_split = line.split(" ", 1)
        if line_split[0] == "PICKLE":
            try:
                nbytes = int(line_split[1])
            except (ValueError, TypeError):
                raise
            else:
                package, self.extra = self.es.read_bytes(nbytes, self.extra)
                line, self.extra = self.es.read_line(self.extra)
                try:
                    data = pickle.loads(package)
                except pickle.PickleError, e:
                    print "Error unpickling object: ", e
                    return None
                else:
                    if line == "PULL OK":
                        return data
                    else:
                        return None
        else:
            # For other data types
            pass

    def result(self, number=None):
        """Gets a specific result from the kernel, returned as a tuple."""
        self._checkConnection()    
    
        if number is None:
            self.es.write_line("RESULT")
        else:
            self.es.write_line("RESULT %i" % number)
        line, self.extra = self.es.read_line(self.extra)
        line_split = line.split(" ", 1)
        if line_split[0] == "PICKLE":
            try:
                nbytes = int(line_split[1])
            except (ValueError, TypeError):
                raise
            else:
                package, self.extra = self.es.read_bytes(nbytes, self.extra)
                line, self.extra = self.es.read_line(self.extra)
                try:
                    data = pickle.loads(package)
                except pickle.PickleError, e:
                    print "Error unpickling object: ", e
                    return None
                else:
                    if line == "RESULT OK":
                        return data
                    else:
                        return None
        else:
            # For other data types
            return False
        
    def status(self):
        """Check the status of the kernel."""
        self._checkConnection()

        self.es.write_line("STATUS")
        line, self.extra = self.es.read_line(self.extra)
        line_split = line.split(" ", 1)
        if line_split[0] == "PICKLE":
            try:
                nbytes = int(line_split[1])
            except (ValueError, TypeError):
                raise
            else:
                package, self.extra = self.es.read_bytes(nbytes, self.extra)
                line, self.extra = self.es.read_line(self.extra)
                try:
                    data = pickle.loads(package)
                except pickle.PickleError, e:
                    print "Error unpickling object: ", e
                    return None
                else:
                    if line == "STATUS OK":
                        return data
                    else:
                        return None
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
        self._checkConnection()

        if addr == None:
            host = socket.gethostbyname(socket.gethostname())
            port = 10104
            print "Kernel notification: ", host, port, flag
        else:
            host, port = addr

        if flag:
            self.es.write_line("NOTIFY TRUE %s %s" % (host, port))
        else:
            self.es.write_line("NOTIFY FALSE %s %s" % (host, port))
        line, self.extra = self.es.read_line(self.extra)
        if line == "NOTIFY OK":
            return True
        else:
            return False        
       
    def reset(self):
        """Clear the namespace if the kernel."""
        self._checkConnection()
            
        self.es.write_line("RESET")
        line, self.extra = self.es.read_line(self.extra)
        if line == "RESET OK":
            return True
        else:
            return False      
                           
    def kill(self):
        """Kill the kernel completely."""
        self._checkConnection()    
    
        self.es.write_line("KILL")
        self.s.close()
        del self.s
        del self.es
        return True   

    def disconnect(self):
        """Disconnect from the kernel, but leave it running."""
        if self.isConnected():
            self.es.write_line("DISCONNECT")
            line, self.extra = self.es.read_line(self.extra)
            if line == "DISCONNECT OK":
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
        
        tarball_name, file_string = _tarModule(mod)
        self._pushModuleString(tarball_name, file_string)
            
    def _pushModuleString(self, tarball_name, file_string):
        """This method send a tarball'd module to a kernel."""
        
        self.push('tar_file_string',file_string)
        self.execute("tar_file = open('%s','wb')" % \
            tarball_name, block=False)
        self.execute("tar_file.write(tar_file_string)", block=False)
        self.execute("tar_file.close()", block=False)
        self.execute("import os", block=False)
        self.execute("os.system('tar -xf %s')" % tarball_name)        
            
    # Additional features

    def __getitem__(self, key):
        return self.pull(key)
        
    def __setitem__(self, key, value):
        d = {key: value}
        self.push(**d)

class InteractiveCluster(object):
    """An interface to a set of ipython kernels for parallel computation."""
    
    def __init__(self):
        """Create an empty cluster object."""
        self.count = 0
        self.kernels = []
        self.kernelAddrs = []
        self._block = False
        
    def __add__(first, second):
        """Add two clusters together.
        
        >>> cluster3 = cluster1 + cluster2
        
        Currently, this addition does not eliminate duplicates.
        """
        # Don't simply call start() as I want references to the RemoteKernel
        # objects and not copies.  This preserves connections.
        ic = InteractiveCluster()
        for w in first.kernels:
            ic.kernels.append(w)
        for w in second.kernels:
            ic.kernels.append(w)
        ic.kernelAddrs = first.kernelAddrs + second.kernelAddrs
        ic.count = len(ic.kernels)
        return ic
        
    def setBlock(self, block):
        self._block = block
        for k in self.kernels:
            k.block = self._block
        
    def getBlock(self):
        return self._block
        
    block = property(getBlock, setBlock, doc="Toggles blocking execution")
        
    def subcluster(self, targets):
        ic = InteractiveCluster()
        for w in targets:
            ic.kernels.append(self.kernels[w])
            ic.kernelAddrs.append(self.kernelAddrs[w])
        ic.count= len(ic.kernels)
        return ic
        
    def _parseTargetsArg(self, targets):
        if targets is 'all':
            return range(self.count)
        elif isinstance(targets, list) or isinstance(targets, tuple):
            return targets
        elif isinstance(targets, int):
            return [targets]
        else:
            raise TypeError("Invalid targets specifier")
                   
    def start(self, addrList):
        """Add already running kernels to the cluster.
        
        This method can be called anytime to add new kernels to the cluster.
        
        @arg addr_list:
            A list of (ip, port) tuples of running kernels
        """
        for a in addrList:
            self.kernelAddrs.append(a)
            self.kernels.append(RemoteKernel(a))
        self.count = len(self.kernels)
        
        # Let everyone know about each other
        for k in self.kernels:
            k.connect()
        self.activate()
        self.setBlock(False)
                    
        return True
    
    def remove(self, target):
        """Remove a specific kernel from the cluster.
        
        This does not kill the kernel, it just stops using it.

        @arg kernel_to_remove:
            An integer specifying which kernel to remove
        """
        del self.kernels[target]
        del self.kernelAddrs[target]
        self.count = len(self.kernelAddrs)
        
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
                
    def save(self, clusterName):
        """Saves the cluster information to a file in ~/.ipython.
        
        This method is used to save a cluster and reload it later.  During
        this period, the kernels in the cluster will remain running.  If 
        a kernel is killed or crashes, reloading will not work.
        
        @arg cluster_name:
            A string to name the file
        """
        path_base = get_home_dir()
        file_path = path_base + "/.ipython/" + clusterName
        f = open(file_path,'w')
        print "Saving to: ", file_path
        for a in self.kernelAadrs:
            f.write("%s %i" % (a[0], a[1]))
        f.close()
        
    def load(self, clusterName):
        """Loads a saved cluster.
        
        @arg cluster_name:
            The filename of the saved cluster as a string
        """
        
        isfile = os.path.isfile
        if isfile(clusterName):
            filePath = clusterName
        else:
            pathBase = get_home_dir()
            filePath = pathBase + "/.ipython/" + clusterName
        try:
            rawClusterInfo = file_readlines(filePath)
        except IOError:
            print "Saved cluster not found"
        else:
            print "Loading from: ", filePath
            def processLine(line):
                tmp = line.strip().split(" ")
                return (tmp[0], int(tmp[1])) 
            addrs = [processLine(x) for x in rawClusterInfo]
            self.start(addrs)
        
    # Methods in the official Interface
        
    def kill(self, targets):
        """Kill all the kernels in the cluster."""
        kernelNumbers = self._parseTargetsArg(targets)
        for w in kernelNumbers:
            self.kernels[w].kill()
            
    def killAll(self):
        return self.kill(targets='all')
            
    def push(self, targets, **namespace):
        """Send a python object to the namespace of some kernels.
                
        The kernels argument is used to select which kernels are sent the 
        object.  There are three cases:
        
        kernels is left empty         -> all kernels get the object
        kernels is a list of integers -> only those kernels get it
        kernels is an integer         -> only that kernel gets it
        
        The kernels in the cluster are labeled by integers starting with 0.
                           
        There is also a dictionary style interface to the push command:
                
        >>> ic = InteractiveCluster()
        >>> ic['a'] = 10        # Same as ic.push('a',10)
        >>> ic[1]['a'] = 10     # Same as ic.push('a',10,1)

        @arg value:
            The python object to send
        @arg key:
            What to name the object in the kernel' namespace
        @arg kernels:
            Which kernels to push to.
        """
        kernelNumbers = self._parseTargetsArg(targets)
        nKernels = len(kernelNumbers)
        
        for w in kernelNumbers:
            self.kernels[w].push(**namespace)
             
    def pushAll(self, **namespace):
        return self.push('all', **namespace)
                
    def scatter(self, targets, key, seq, style='basic', flatten=False):
    
        kernelNumbers = self._parseTargetsArg(targets)
        nKernels = len(kernelNumbers)
        
        mapClass = map.styles[style]
        mapObject = mapClass()
        
        for index, item in enumerate(kernelNumbers):
            partition = mapObject.getPartition(seq, index, nKernels)
            if flatten and len(partition) ==1:    
                self.kernels[item].push(**{key: partition[0]})
            else:
                self.kernels[item].push(**{key: partition})                
               
    def scatterAll(self, key, seq, style='basic', flatten=False):
        return self.scatter('all', key, seq, style, flatten)
                   
    def gather(self, targets, key, style='basic'):
    
        kernelNumbers = self._parseTargetsArg(targets)
        nKernels = len(kernelNumbers)
                
        gatheredData = []
        for w in kernelNumbers:
            gatheredData.append(self.kernels[w].pull(key))
        
        mapClass = map.styles[style]
        mapObject = mapClass()
        return mapObject.joinPartitions(gatheredData)
                    
    def gatherAll(self, key, style='basic'):
        return self.gather('all', key, style)
            
    def pull(self, targets, *keys, **options):
        """Get a python object from some kernels.
        
        The kernels argument is used to select which kernels are sent the 
        object.  There are three cases:
        
        kernels is left empty         -> all kernels get the object
        kernels is a list of integers -> only those kernels get it
        kernels is an integer         -> only that kernel gets it
        
        The kernels in the cluster are labeled by integers starting with 0.
                
        If the object does not exist in the kernel's namespace a NotDefined
        object will be returned.
        
        Like push, pull also has a dictionary interface:

        >>> ic = InteractiveCluster()
        >>> ic['a'] = 10        # Same as ic.push('a',10)
        >>> ic['a']             # Same as ic.pull(10,'a')
        [10, 10, 10, 10]
        >>> ic[0]['a']          # Same as ic.pull(10, 'a', 0)
        10
        
        @arg key:
            The name of the python object to get
        @arg kernels:
            Which kernels to get the object from to.
        """
        flatten = options.get('flatten', None)    
        results = []
        kernelNumbers = self._parseTargetsArg(targets)
        for w in kernelNumbers:
            results.append(self.kernels[w].pull(*keys))
        if flatten:
            return genutil_flatten(results)
        else:
            return results
            
    def pullAll(self, *keys, **options):
        return self.pull('all', *keys, **options)
            
    def execute(self, targets, lines, block=False):
        """Execute python source code on the ipython kernel.
                
        The kernels argument is used to select which kernels are sent the 
        object.  There are three cases:
        
        kernels is left empty         -> all kernels get the object
        kernels is a list of integers -> only those kernels get it
        kernels is an integer         -> only that kernel gets it
        
        The kernels in the cluster are labeled by integers starting with 0.
        
        The execute command also has a magic syntax.  Once a cluster has been
        made active using the activate() method, the %px and %autopx magics
        will work for the cluster:
        
        >>> %px a = 5           # Same as execute('a=5')
        >>> %autopx             # Toggles autoparallel mode on
                                # Now every comic.mand is wrapped in execute()
        >>> %autopx             # Toggles autoparallel mode off

        @arg source:
            A string containing valid python code
        @arg kernels:
            Which kernels to get the object from to.
        """
        kernelNumbers = self._parseTargetsArg(targets)
        for w in kernelNumbers:
            self.kernels[w].execute(lines, block=block)

    def executeAll(self, lines, block=False):
        return self.execute('all', lines, block=block)

    def run(self, targets, filename):
        """Run a file on a set of kernels."""
        kernelNumbers = self._parseTargetsArg(targets)
        fileobj = open(filename, 'r')
        source = fileobj.read()
        fileobj.close()
        # if the compilation blows, we get a local error right away
        code = compile(source, filename, 'exec')
        
        # Now run the code
        for w in kernelNumbers:
            self.kernels[w].execute(source)

    def runAll(self, filename):
        return self.run('all', filename)

    def status(self, targets):
        """Get the status of a set of kernels."""
        kernelNumbers = self._parseTargetsArg(targets)
        result = []
        for w in kernelNumbers:
            result.append(self.kernels[w].status())
        return result
        
    def statusAll(self):
        return self.status('all')
        
    def notify(self, targets, addr=None, flag=True):
        """Instruct a set of kernels to notify a result gatherer."""
        kernelNumbers = self._parseTargetsArg(targets)
        for w in kernelNumbers:
            self.kernels[w].notify(addr, flag)

    def notifyAll(self, addr=None, flag=True):
        return self.notify('all', addr, flag)

    def reset(self, targets):
        """Reset the namespace of a set of kernels."""
        kernelNumbers = self._parseTargetsArg(targets)
        for w in kernelNumbers:
            self.kernels[w].reset()
            
    def resetAll(self):
        return self.reset('all')
            
    def disconnect(self, targets):
        """Disconnect from a set of kernels."""
        kernelNumbers = self._parseTargetsArg(targets)
        for w in kernelNumbers:
            self.kernels[w].disconnect()    

    def disconnectAll(self):
        return self.disconnect('all')

    def pushModule(self, mod):
        """Send a locally imported module to a kernel.
        
        This method makes a tarball of an imported module that exists 
        on the local host and sends it to the working directory of the
        kernels in the cluster.  It then untars it.  
        
        After that, the module can be imported and used by the kernels.
        
        Notes:
        
        - It DOES NOT handle eggs yet.
        
        - The file must fit in the available RAM.
    
        - It will handle both single module files, as well as packages.
    
        - The byte code files (*.pyc) are not deleted.
    
        - It has not been tested with modules containing extension code,
          but it should work in most cases.
      
        - There are cross platform issues. 
        """
    
        tarballName, fileString = _tarModule(mod)
        for w in self.kernels:
            w._pushModuleString(tarballName, fileString)
    
    # Additional features that might end up in the interface
    
    def __setitem__(self, key, value):
        if isinstance(key, str):
            self._push(key, value)
        else:
            raise ValueError
        
    def __getitem__(self, key):
        if isinstance(key, int):
            return self.kernels[key]
        elif isinstance(key, str):
            return self.pull(key)
        elif isinstance(key, slice):
            return self.subcluster(range(*key.indices(self.count)))
            
    def __len__(self):
        return self.count
        
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
        self.scatter(targets, '_ipython_map_seq', seq, style='basic')
        sourceToRun = \
            '_ipython_map_seq_result = map(%s, _ipython_map_seq)' % \
            functionSource
        self.execute(targets, sourceToRun)
        return self.gather(targets, '_ipython_map_seq_result', style='basic')
        
    def mapAll(self, functionSource, seq, style='basic'):
        return self.map('all', functionSource, seq, style)
        
    def reduce(self, targets, localFunction, sequenceName):
        result = self.gather(targets, sequenceName)
        return reduce(localFunction, result)
                
    def reduceAll(self, localFunction, sequenceName):
        return self.reduce('all', localFunction, sequenceName)
                
    def parallelize(self, functionName):
        """Contruct and return a parallelized function.
        
        The resulting ParallelFunction object is a callable that can operates 
        on sequences.  
        
        @arg func_name:
            The name of the function to parallelize.  
            It must be defined in the namespace of the kernel.
        """
        return ParallelFunction(functionName, self)
    
    def msg(self, txt):
        # XXX getlogin is very mysteriously failing under ubuntu.  Protect 
        # with a hack for now
        try:
            user = os.getlogin()
        except:
            user = 'user'

        self.kernels[0].push('__ipmsg',"[%s]: %s" % (user, txt))
        self.kernels[0].execute("print __ipmsg,")
                  
