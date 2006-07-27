# -*- test-case-name: ipython1.test.test_controllerclient -*-
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

from twisted.internet import defer

from IPython.ColorANSI import *
from IPython.genutils import flatten as genutil_flatten

from ipython1.kernel1p.scatter import *
from ipython1.kernel1p.parallelfunction import ParallelFunction

try:
    from ipython1.kernel1p.esocket import LineSocket
except ImportError:
    print "ipython1 needs to be in your PYTHONPATH"
    
try:
    import ipython1.kernel1p.kernel_magic
except ImportError:
    print "ipython1 needs to be in your PYTHONPATH"

try:
    from ipython1.kernel1p.kernelerror import NotDefined
except ImportError:
    print "ipython1 needs to be in your PYTHONPATH"

#from esocket import LineSocket
#import kernel_magic
#from kernelerror import NotDefined
           
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
        self.extra = ''
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
                
        self.es = LineSocket(self.s)
        # Turn of Nagle's algorithm to prevent the 200 ms delay :)
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY,1)
    
    def execute(self, source, id='all', block=False):
        """Execute python source code on the ipython kernel.
        
        @arg source:
            A string containing valid python code
        """
        self._check_connection()
        if isinstance(id, list):
            id = '::'.join(map(str, id))
        if self.block or block:
            self.es.write_line("EXECUTE BLOCK %s::%s" % (source, id))
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
                for d in data:
                    cmd_num = d[0]
                    cmd_stdin = d[1]
                    cmd_stdout = d[2][:-1]
                    cmd_stderr = d[3][:-1]
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
            string = "EXECUTE %s::%s" % (source, id)
            self.es.write_line(string)
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
    
    def push(self, key, value, id='all'):
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
        if isinstance(id, list):
            id = '::'.join(map(str, id))
        try:
            package = pickle.dumps(value, 2)
        except pickle.PickleError, e:
            print "Object cannot be pickled: ", e
            return False
        self.es.write_line("PUSH %s::%s" % (key, id))
        self.es.write_line("PICKLE %i" % len(package))
        self.es.write_bytes(package)
        line, self.extra = self.es.read_line(self.extra)
        if line == "PUSH OK":
            return True
        if line == "PUSH FAIL":
            return False
    
    def update(self, dic, id='all'):
        """Send the dict of key value pairs to the kernel's namespace.
        
        >>> rc = RemoteController(addr)
        >>> rc.update({'a':1,'b':2,'c':'mystring}, [1,2,3])    
        # sends a, b and c to the engines 1,2,3
        
        @arg dic:
            A dictionary of key, value pairs to send to the kernel
        """
        self._check_connection()
        if isinstance(id, list):
            id = '::'.join(map(str, id))
        try:
            package = pickle.dumps(dic, 2)
        except pickle.PickleError, e:
            print "Object cannot be pickled: ", e
            return False
        self.es.write_line("UPDATE %s::%s" % (dic, id))
        self.es.write_line("PICKLE %i" % len(package))
        self.es.write_bytes(package)
        line, self.extra = self.es.read_line(self.extra)
        if line == "UPDATE OK":
            return True
        if line == "UPDATE FAIL":
            return False
    
    def __setitem__(self, key, value):
        self.push(key, value)
    
    def pull(self, key, id = 'all'):
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
        if isinstance(id, list):
            id = '::'.join(map(str, id))
        
        self.es.write_line("PULL %s::%s" % (key, id))
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
    
    def getCommand(self, number=None, id='all'):
        """Gets a specific result from the kernel, returned as a tuple."""
        self._check_connection()    
        if isinstance(id, list):
            id = '::'.join(map(str, id))
        
        if number is None:
            self.es.write_line("GETCOMMAND ::%s" %id)
        else:
            self.es.write_line("GETCOMMAND %i::%s" % (number, id))
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
                    if line == "GETCOMMAND OK":
                        return data
                    else:
                        return None
        else:
            # For other data types
            return False
    
    def getLastCommandIndex(self, id='all'):
        """Gets the index of the last command."""
        self._check_connection()    
        if isinstance(id, list):
            id = '::'.join(map(str, id))

        self.es.write_line("GETLASTCOMMANDINDEX ::%s" %id)
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
                    if line == "GETLASTCOMMANDINDEX OK":
                        return data
                    else:
                        return None
        else:
            # For other data types
            return False

    def status(self, id='all'):
        """Check the status of the kernel."""
        self._check_connection()
        if isinstance(id, list):
            id = '::'.join(map(str, id))
        
        self.es.write_line("STATUS ::%s" %id)
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
    
    def reset(self, id='all'):
        """Clear the namespace if the kernel."""
        self._check_connection()
        if isinstance(id, list):
            id = '::'.join(map(str, id))
        
        self.es.write_line("RESET ::%s" %id)
        line, self.extra = self.es.read_line(self.extra)
        if line == "RESET OK":
            return True
        else:
            return False      
    
    def kill(self, id='all'):
        """Kill the engine completely."""
        self._check_connection()    
        if isinstance(id, list):
            id = '::'.join(map(str, id))
        
        self.es.write_line("KILL ::%s" %id)
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
                print line
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
    

    
