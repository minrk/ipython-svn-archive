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

from ipython1.kernel.scatter import *
from ipython1.kernel.parallelfunction import ParallelFunction

from ipython1.kernel.esocket import LineSocket
import ipython1.kernel.kernel_magic
from ipython1.kernel.kernelerror import NotDefined
           
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
    file_string = tar_file.read()
    tar_file.close()
    
    # Remove the local copy of the tarball
    #os.system("rm %s" % tarball_name)
    
    return tarball_name, file_string
                    
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
        
    def execute(self, source, block=False):
        """Execute python source code on the ipython kernel.
        
        @arg source:
            A string containing valid python code
        """
        self._check_connection()
        if self.block or block:
            self.es.write_line("EXECUTE BLOCK %s" % source)
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
            self.es.write_line("EXECUTE %s" % source)
            line, self.extra = self.es.read_line(self.extra)
            data = None
             
        if line == "EXECUTE OK":
            return None
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
        
    def push(self, key, value, forward=False):
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
        self._check_connection()
        try:
            package = pickle.dumps(value, 2)
        except pickle.PickleError, e:
            print "Object cannot be pickled: ", e
            return False
        if forward:
            self.es.write_line("PUSH FORWARD %s" % key)
        else:
            self.es.write_line("PUSH %s" % key )
        self.es.write_line("PICKLE %i" % len(package))
        self.es.write_bytes(package)
        line, self.extra = self.es.read_line(self.extra)
        if line == "PUSH OK":
            return True
        if line == "PUSH FAIL":
            return False
        
    def update(self,dict):
        """Send the dict of key value pairs to the kernel's namespace.
        
        >>> rk = RemoteKernel(addr)
        >>> rk.update({'a':1,'b':2,'c':'mystring})    
        # sends a, b and c to the kernel
        
        @arg dict:
            A dictionary of key, value pairs to send to the kernel
        """
        for key in dict.keys():
            self.push(key,dict[key])
        
    def __setitem__(self, key, value):
        self.push(key, value)
        
    def pull(self, key):
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
        self._check_connection()    
    
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

    def __getitem__(self, key):
        return self.pull(key)

    def result(self, number=None):
        """Gets a specific result from the kernel, returned as a tuple."""
        self._check_connection()    
    
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
        
    def move(keya, keyb, target):
        """Move a python object from one kernel to another.
        
        Not implemented.
        """
        self._check_connection()
        print "Mpve is not implemented yet."
        #write_line("MOVE %s %s %" % (keya, keyb, target))
        #read_line()

    def status(self):
        """Check the status of the kernel."""
        self._check_connection()

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

    def allow(self, ip):
        """Instruct the kernel to allow connections from an ip address.
                
        By default kernels allow only connections from the localhost and one
        other ip address specified when the kernel is started.  Thus, this 
        method must be used to add other allowed ip addresses.

        @arg ip:
            An ip address to allow.
        @type ip: str
        """
        self._check_connection()
        
        self.es.write_line("ALLOW TRUE %s" % ip)
        line, self.extra = self.es.read_line(self.extra)
        if line == "ALLOW OK":
            return True
        else:
            return False      

    def deny(self, ip):
        """Instruct the kernel to not allow connections from an ip address.
        
        IP addresses are denied by default, so this method only needs to be
        called to deny access to an ip that was allowed with allow().

        @arg ip:
            An ip address to deny.
        @type ip: str 
        """
        self._check_connection()
        
        self.es.write_line("ALLOW FALSE %s" % ip)
        line, self.extra = self.es.read_line(self.extra)
        if line == "ALLOW OK":
            return True
        else:
            return False      

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
       
    def cluster(self, addrs=None):
        """Instruct the kernel to participate in a cluster.
        
        IPython kernels can be grouped into clusters.  This is typically
        done using InteractiveCluster intances.  The cluster() method is
        provided to allow each kernel to be notified of the addresses of 
        the other kernels in its cluster.
   
        @arg addrs:
            A list of (ip, port) tuples of the other kernels in the cluster
        """
        self._check_connection()
        if addrs is None:
            self.es.write_line("CLUSTER CLEAR")
            line, self.extra = self.es.read_line(self.extra)
            if line == "CLUSTER OK":
                return True
            if line == "CLUSTER FAIL":
                return False
        else:
            try:
                package = pickle.dumps(addrs, 2)
            except pickle.PickleError, e:
                print "Pass a valid python list of addresses: ", e
                return False
            else:
                self.es.write_line("CLUSTER CREATE")
                self.es.write_line("PICKLE %i" % len(package))
                self.es.write_bytes(package)
                line, self.extra = self.es.read_line(self.extra)
                if line == "CLUSTER OK":
                    return True
                if line == "CLUSTER FAIL":
                    return False

    def reset(self):
        """Clear the namespace if the kernel."""
        self._check_connection()
            
        self.es.write_line("RESET")
        line, self.extra = self.es.read_line(self.extra)
        if line == "RESET OK":
            return True
        else:
            return False      
                           
    def kill(self):
        """Kill the kernel completely."""
        self._check_connection()    
    
        self.es.write_line("KILL")
        self.s.close()
        del self.s
        del self.es
        return True   

    def disconnect(self):
        """Disconnect from the kernel, but leave it running."""
        if self.is_connected():
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
        
        tarball_name, file_string = _tar_module(mod)
        self._push_module_string(tarball_name, file_string)
            
    def _push_module_string(self, tarball_name, file_string):
        """This method send a tarball'd module to a kernel."""
        
        self.push('tar_file_string',file_string)
        self.execute("tar_file = open('%s','wb')" % \
            tarball_name, block=False)
        self.execute("tar_file.write(tar_file_string)", block=False)
        self.execute("tar_file.close()", block=False)
        self.execute("import os", block=False)
        self.execute("os.system('tar -xf %s')" % tarball_name)        
            
class InteractiveCluster(object):
    """An interface to a set of ipython kernels for parallel computation."""
    def __init__(self):
        """Create an empty cluster object."""
        self.count = 0
        self.kernels = []
        self.kernel_addrs = []
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
        ic.kernel_addrs = first.kernel_addrs + second.kernel_addrs
        ic.count = len(ic.kernels)
        ic._cluster()
        return ic
        
    def set_block(self, block):
        self._block = block
        for k in self.kernels:
            k.block = self._block
        
    def get_block(self):
        return self._block
        
    block = property(get_block, set_block, doc="Toggles blocking execution")
        
    def subcluster(self, kernel_list):
        ic = InteractiveCluster()
        for w in kernel_list:
            ic.kernels.append(self.kernels[w])
            ic.kernel_addrs.append(self.kernel_addrs[w])
        ic.count= len(ic.kernels)
        return ic
        
    def _parse_kernels_arg(self, kernels):
        if kernels is None:
            return range(self.count)
        elif isinstance(kernels, list) or isinstance(kernels, tuple):
            return kernels
        elif isinstance(kernels, int):
            return [kernels]
     
    def _cluster(self):
        """Notify each kernel in the cluster about the other kernels."""
        for w in self.kernels:
            w.cluster(self.kernel_addrs)
              
    def start(self, addr_list):
        """Add already running kernels to the cluster.
        
        This method can be called anytime to add new kernels to the cluster.
        
        @arg addr_list:
            A list of (ip, port) tuples of running kernels
        """
        for a in addr_list:
            self.kernel_addrs.append(a)
            self.kernels.append(RemoteKernel(a))
        self.count = len(self.kernels)
        
        # Let everyone know about each other
        self._cluster()
        self.activate()
                    
        return True
    
    def remove(self, kernel_to_remove):
        """Remove a specific kernel from the cluster.
        
        This does not kill the kernel, it just stops using it.

        @arg kernel_to_remove:
            An integer specifying which kernel to remove
        """
        del self.kernels[kernel_to_remove]
        del self.kernel_addrs[kernel_to_remove]
        self.count = len(self.kernel_addrs)
        self._cluster()
        
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
                
    def save(self, cluster_name):
        """Saves the cluster information to a file in ~/.ipython.
        
        This method is used to save a cluster and reload it later.  During
        this period, the kernels in the cluster will remain running.  If 
        a kernel is killed or crashes, reloading will not work.
        
        @arg cluster_name:
            A string to name the file
        """
        path_base = os.path.expanduser("~/.ipython")
        file_path = path_base + "/" + cluster_name
        f = open(file_path,'w')
        print "Saving to: ", file_path
        pickle.dump(self.kernel_addrs, f, 1)
        f.close()
        
    def load(self, cluster_name):
        """Loads a saved cluster.
        
        @arg cluster_name:
            The filename of the saved cluster as a string
        """
        path_base = os.path.expanduser("~/.ipython")
        file_path = path_base + "/" + cluster_name
        try:
            f = open(file_path,'r')
        except IOError:
            print "Saved cluster not found"
        else:
            print "Loading from: ", file_path
            addrs = pickle.load(f)
            f.close()
            self.start(addrs)        

    # XXX - fperez: finish after scipy, b/c I'll make use of changed
    # functionality in genutils, only available to svn users
    def __load00(self, cluster_name):
        """Loads a saved cluster.
        
        @arg cluster_name:
            The filename of the saved cluster as a string
        """
        isfile = os.path.isfile
        if isfile(cluster_name):
            file_path = cluster_name
        else:
            path_base = os.path.expanduser("~/.ipython")
            file_path = path_base + "/" + cluster_name
        try:
            f = open(file_path,'r')
        except IOError:
            print "Saved cluster not found"
        else:
            print "Loading from: ", file_path
            addrs = pickle.load(f)
            f.close()
            self.start(addrs)        
        
    def __getitem__(self, key):
        if isinstance(key, int):
            return self.kernels[key]
        elif isinstance(key, str):
            return self.pull(key)
            
    def __len__(self):
        return self.count
        
    def kill(self):
        """Kill all the kernels in the cluster."""
        for w in self.kernels:
            w.kill()
            
    def push(self, key, value, kernels=None):
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
        kernel_numbers = self._parse_kernels_arg(kernels)
        n_kernels = len(kernel_numbers)
        
        if isinstance(value, Scatter):
            for index, item in enumerate(kernel_numbers):
                self.kernels[item].push(key,
                    value.partition(index,n_kernels))
        else:
            for w in kernel_numbers:
                self.kernels[w].push(key, value)
                
    def __setitem__(self, key, value):
        if isinstance(key, str):
            self.push(key, value)
        else:
            raise ValueError
            
    def update(self, dict, kernels=None):
        """Send the dict of key, value pairs to the kernels."""
        
        kernel_numbers = self._parse_kernels_arg(kernels)
        n_kernels = len(kernel_numbers)
        for w in kernel_numbers:
            self.kernels[w].update(dict)
            
    def pull(self, key, flatten=False, kernels=None):
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
        results = []
        kernel_numbers = self._parse_kernels_arg(kernels)
        for w in kernel_numbers:
            results.append(self.kernels[w].pull(key))
        if flatten:
            return genutil_flatten(results)
        else:
            return results
            
    def execute(self, source, block=False, kernels=None):
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
        kernel_numbers = self._parse_kernels_arg(kernels)
        for w in kernel_numbers:
            self.kernels[w].execute(source,block=block)

    def run(self, fname, kernels=None):
        """Run a file on a set of kernels."""
        kernel_numbers = self._parse_kernels_arg(kernels)
        fileobj = open(fname,'r')
        source = fileobj.read()
        fileobj.close()
        # if the compilation blows, we get a local error right away
        code = compile(source,fname,'exec')
        
        # Now run the code
        for w in kernel_numbers:
            self.kernels[w].execute(source)

    def status(self, kernels=None):
        """Get the status of a set of kernels."""
        kernel_numbers = self._parse_kernels_arg(kernels)
        result = []
        for w in kernel_numbers:
            result.append(self.kernels[w].status())
        return result
        
    def notify(self, addr=None, flag=True, kernels=None):
        """Instruct a set of kernels to notify a result gatherer."""
        kernel_numbers = self._parse_kernels_arg(kernels)
        for w in kernel_numbers:
            self.kernels[w].notify(addr, flag)

    def allow(self, ip, kernels=None):
        """Instruct a set of kernels to allow connections from an ip."""
        kernel_numbers = self._parse_kernels_arg(kernels)
        for w in kernel_numbers:
            self.kernels[w].allow(ip)

    def deny(self, ip, kernels=None):
        """Instruc a set of kernels to deny connections from an ip."""
        kernel_numbers = self._parse_kernels_arg(kernels)
        for w in kernel_numbers:
            self.kernels[w].deny(ip)

    def reset(self, kernels=None):
        """Reset the namespace of a set of kernels."""
        kernel_numbers = self._parse_kernels_arg(kernels)
        for w in kernel_numbers:
            self.kernels[w].reset()
            
    def disconnect(self, kernels=None):
        """Disconnect from a set of kernels."""
        kernel_numbers = self._parse_kernels_arg(kernels)
        for w in kernel_numbers:
            self.kernels[w].disconnect()    

    def push_module(self, mod):
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
    
        tarball_name, file_string = _tar_module(mod)
        for w in self.kernels:
            w._push_module_string(tarball_name, file_string)
    
    def map(self, func_code, seq):
        """A parallelized version of python's builtin map.
        
        This version of map is designed to work similarly to python's
        builtin map(), but the execution is done in parallel on the cluster.
                
        Example:
        
        >>> map('lambda x: x*x', range(10000))

        @arg func_code:
            A string of python code representing a callable.
            It must be defined in the kernels namespace.
        @arg seq:
            A python sequence to call the callable on
        """
        self.push('_ipython_map_seq', Scatter(seq))
        source_to_run = \
            '_ipython_map_seq_result = map(%s, _ipython_map_seq)' % \
            func_code
        self.execute(source_to_run)
        return self.pull('_ipython_map_seq_result',flatten=True)
        
    def msg(self, txt):
        # XXX getlogin is very mysteriously failing under ubuntu.  Protect 
        # with a hack for now
        try:
            user = os.getlogin()
        except:
            user = 'user'
        
        self.kernels[0].push('__ipmsg',"[%s]: %s" % (user, txt))
        self.kernels[0].execute("print __ipmsg,")
        
    def parallelize(self, func_name):
        """Contruct and return a parallelized function.
        
        The resulting ParallelFunction object is a callable that can operates 
        on sequences.  
        
        @arg func_name:
            The name of the function to parallelize.  
            It must be defined in the namespace of the kernel.
        """
        return ParallelFunction(func_name, self)
    
                  
